from django.contrib.auth.models import User

from core.models import (
    Assignment,
    Project,
    EvaluatorProfile
)


MIN_EVALUATORS_PER_PROJECT = 3


def distribute_projects():

    projects = Project.objects.all()

    for project in projects:

        current_assignments = Assignment.objects.filter(
            project=project
        ).count()

        needed = MIN_EVALUATORS_PER_PROJECT - current_assignments

        if needed <= 0:
            continue

        eligible_evaluators = User.objects.filter(
            evaluatorprofile__axis=project.axis
        ).distinct()

        eligible_evaluators = sorted(
            eligible_evaluators,
            key=lambda evaluator: Assignment.objects.filter(
                evaluator=evaluator
            ).count()
        )

        assigned = 0

        for evaluator in eligible_evaluators:

            if assigned >= needed:
                break

            already_assigned = Assignment.objects.filter(
                evaluator=evaluator,
                project=project
            ).exists()

            if already_assigned:
                continue

            current_load = Assignment.objects.filter(
                evaluator=evaluator
            ).count()

            max_projects = evaluator.evaluatorprofile.max_projects

            if current_load >= max_projects:
                continue

            Assignment.objects.create(
                evaluator=evaluator,
                project=project
            )

            assigned += 1