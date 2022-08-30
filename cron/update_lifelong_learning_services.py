import copy
import json
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

        count = {
            "reviewed": 0,
            "created": 0,
            "modified": 0,
            "deactivated": 0
        }
        treated_ids = []

        # Get the INFPC entity

        entity = self.db.session.query(self.db.tables["Entity"]) \
            .filter(func.lower(self.db.tables["Entity"].name).like("%INFPC%")) \
            .all()

        if len(entity) == 0:
            return [], "500 INFPC entity not found"
        if len(entity) > 1:
            return [], "500 Too many INFPC entity found"

        entity = entity[0]

        # Get the 'Training' taxonomy value

        training_tags = self.db.session.query(self.db.tables["TaxonomyValue"]) \
            .filter(func.lower(self.db.tables["TaxonomyValue"].name).like("Training")) \
            .filter(func.lower(self.db.tables["TaxonomyValue"].category).like("SERVICE CATEGORY")) \
            .all()

        if len(training_tags) == 0:
            return [], "500 'TRAINING' value in the 'SERVICE CATEGORY' taxonomy not found"

        training_tag = training_tags[0]

        # Treat the data

        external_references = [a["id"] for a in data["trainings"]]

        db_services = self.db.get(
            self.db.tables["Article"],
            {"external_reference": external_references}
        )

        for source_service in data["trainings"]:
            if source_service["id"] not in treated_ids:
                treated_ids.append(source_service["id"])

                db_article = [a for a in db_services if str(source_service["id"]) == a.external_reference]
                db_article = db_article[0] if len(db_article) > 0 else self.db.tables["Article"]()

                count["reviewed"] += 1
                count["created"] += 1 if db_article.id is None else 0

                db_article, m1 = self._manage_service(db_article, source_service, entity, training_tag)

                count["modified"] += 1 if (db_article.id is not None and m1) else 0

        # Deactivate the missing services

        self._deactivate_deprecated_services(entity, external_references)

        # Send response

        status = f"200 Success: {count['reviewed']} treated, {count['created']} created, " \
            f"{count['modified']} modified, {count['deactivated']} deactivated"

        return Response(status=status)

    def _manage_service(self, a, source, entity, training_tag):
        copied_a = copy.deepcopy(a)

        handle = f"{source['id']}"

        # Insert data into Article object

        a.external_reference = source["id"] if a.external_reference is None else a.external_reference
        a.title = source['title'] if a.title is None else a.title
        a.description = UpdateLifelongLearningServices._get_description(source) if a.title is None else a.title
        a.handle = handle if a.handle is None else a.handle
        a.type = "SERVICE" if a.type is None else a.type
        a.status = "PUBLIC" if a.status is None else a.status
        a.link = source["link"] if a.link is None else a.link
        a.is_created_by_admin = True

        # Save modifications in DB

        article = self.db.merge(a, self.db.tables["Article"])
        is_modified = not self.db.are_objects_equal(a, copied_a, self.db.tables["Article"])

        # Add the Moovijob relationship if it does not exist

        tags = self.db.get(self.db.tables["ArticleEntityTag"], {"entity_id": entity.id, "article_id": article.id})

        if len(tags) == 0:
            self.db.insert({"entity_id": entity.id, "article_id": article.id}, self.db.tables["ArticleEntityTag"])

        # Add the Training tag if it does not exist

        tags = self.db.get(
            self.db.tables["ArticleTaxonomyTag"],
            {"taxonomy_value_id": training_tag.id, "article_id": article.id}
        )

        if len(tags) == 0:
            self.db.insert(
                {"taxonomy_value_id": training_tag.id, "article_id": article.id},
                self.db.tables["ArticleTaxonomyTag"]
            )

        return article, is_modified

    def _deactivate_deprecated_services(self, entity, external_references):
        subquery = self.db.session.query(self.db.tables["ArticleEntityTag"]) \
            .with_entities(self.db.tables["ArticleEntityTag"].article_id) \
            .filter(self.db.tables["ArticleEntityTag"].entity_id == entity.id) \
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
    def _get_description(source):
        description = ""

        if source["entity"] is not None and len(source["entity"]) > 0:
            description += f"Entity: {source['entity']} \u2014 "
        if source["durationInHours"] is not None and len(str(source["durationInHours"])) > 0:
            description += f"Duration in hours: {str(source['durationInHours'])} \u2014 "
        if source["trainingLevelTitle"] is not None and len(source["trainingLevelTitle"]) > 0:
            description += f"Level: {source['entity']} \u2014 "

        if len(description) > 0:
            description = description[:-3]

        return description
