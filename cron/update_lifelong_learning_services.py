import copy
import json
import re
from urllib3 import ProxyManager
from urllib import request
from flask import Response

from sqlalchemy import func

from config.config import HTTP_PROXY
from decorator.log_task import log_task


class UpdateLifelongLearningServices:

    def __init__(self, db):
        self.db = db

    @log_task
    def run(self):  # pylint: disable=too-many-locals

        base_url = "https://api.formator.lu/search/cybersecuritytrainings/en"

        if HTTP_PROXY is not None:
            http = ProxyManager(HTTP_PROXY)
            response = http.request('GET', base_url)
            content = response.data
        else:
            response = request.urlopen(base_url)  # nosec
            content = response.read()

        data = json.loads(content)

        external_references = []

        count = {
            "reviewed": 0,
            "created": 0,
            "modified": 0,
            "deactivated": 0
        }

        # Get the Moovijob company

        entity = self.db.session.query(self.db.tables["Company"]) \
            .filter(func.lower(self.db.tables["Company"].name).like("%INFPC%")) \
            .all()

        if len(entity) == 0:
            return [], "500 INFPC entity not found"
        if len(entity) > 1:
            return [], "500 Too many INFPC entity found"

        entity = entity[0]

        # Treat the data

        external_references = [str(a["id"]) for a in data["data"]]

        db_services = self.db.get(
            self.db.tables["Article"],
            {"external_reference": external_references}
        )

        for source_service in data["data"]:

            db_article = [a for a in db_services if str(source_service["id"]) == a.external_reference]
            db_article = db_article[0] if len(db_article) > 0 else self.db.tables["Article"]()

            count["reviewed"] += 1
            count["created"] += 1 if db_article.id is None else 0

            db_article, m1 = self._manage_service(db_article, source_service, entity)
            db_article_version, m2 = self._manage_article_version(db_article)
            _, m3 = self._manage_article_version_box(db_article_version, source_service)

            count["modified"] += 1 if (db_article.id is not None and (m1 or m2 or m3)) else 0

        # Deactivate the missing services

        self._deactivate_deprecated_services(entity, external_references)

        # Send response

        status = f"200 Success: {count['reviewed']} treated, {count['created']} created, " \
            f"{count['modified']} modified, {count['deactivated']} deactivated"

        return Response(status=status)

    def _manage_service(self, a, source, company):
        copied_a = copy.deepcopy(a)

        title = self._get_preferred_lang_info(source['title'])
        handle = f"{source['id']}-{re.sub(r'[^a-z1-9-]', '', title.lower().replace(' ', '-'))[:80]}"

        # Insert data into Article object

        a.external_reference = source["id"] if a.external_reference is None else a.external_reference
        a.title = title if a.title is None else a.title
        a.handle = handle if a.handle is None else a.handle
        a.type = "JOB OFFER" if a.type is None else a.type
        a.publication_date = source["published_at"].split("T")[0] if a.publication_date is None else a.publication_date
        a.status = "PUBLIC" if a.status is None else a.status
        a.link = self._get_preferred_lang_info(source["urls"]) if a.link is None else a.link
        a.is_created_by_admin = True

        # Save modifications in DB

        article = self.db.merge(a, self.db.tables["Article"])
        is_modified = not self.db.are_objects_equal(a, copied_a, self.db.tables["Article"])

        # Add the Moovijob relationship if it does not exist

        tags = self.db.get(self.db.tables["ArticleCompanyTag"], {"company": company.id, "article": article.id})

        if len(tags) == 0:
            self.db.insert({"company": company.id, "article": article.id}, self.db.tables["ArticleCompanyTag"])

        return article, is_modified

    def _deactivate_deprecated_services(self, company, external_references):
        subquery = self.db.session.query(self.db.tables["ArticleCompanyTag"]) \
            .with_entities(self.db.tables["ArticleCompanyTag"].article) \
            .filter(self.db.tables["ArticleCompanyTag"].company == company.id) \
            .subquery()

        offers_to_archive = self.db.session.query(self.db.tables["Article"]) \
            .filter(self.db.tables["Article"].status == "PUBLIC") \
            .filter(self.db.tables["Article"].id.in_(subquery)) \
            .filter(self.db.tables["Article"].external_reference.notin_(external_references)) \
            .all()

        if len(offers_to_archive) > 0:
            for o in offers_to_archive:
                o.status = "ARCHIVE"

            self.db.merge(offers_to_archive, self.db.tables["Article"])

    @staticmethod
    def _get_preferred_lang_info(lang_dict):
        if "en" in lang_dict and lang_dict["en"] is not None:
            return lang_dict["en"]
        if "fr" in lang_dict and lang_dict["fr"] is not None:
            return lang_dict["fr"]
        if "de" in lang_dict and lang_dict["de"] is not None:
            return lang_dict["de"]
        if len(lang_dict.keys()) > 0:
            return lang_dict[list(lang_dict.keys())[0]]
        return None
