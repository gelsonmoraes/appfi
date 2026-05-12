from django.utils import timezone
from django.db.models import Avg
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

# ---------------------------
# SUPPORT TABLES
# ---------------------------

class Axis(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name
    
class SystemConfig(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Config {self.id}"

class CriterionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class School(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
class Grade(models.Model):
    name = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return self.name

class EducationalLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# ---------------------------
# MAIN ENTITIES
# ---------------------------

class Project(models.Model):
    title = models.CharField(max_length=255)
    student_name = models.CharField(max_length=255)
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )    
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    educational_level = models.ForeignKey(
        EducationalLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    axis = models.ForeignKey(Axis, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Criterion(models.Model):

    CATEGORY_CHOICES = [
        ('project', 'Project'),
        ('presentation', 'Presentation'),
        ('materials', 'Materials'),
        ('highlight', 'Highlight'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        CriterionCategory,
        on_delete=models.CASCADE
    )
    is_highlight = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class EvaluatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    axis = models.ForeignKey(Axis, on_delete=models.CASCADE)
    max_projects = models.IntegerField(default=100)
    
    def __str__(self):
        return f"{self.user} - {self.axis}"

# ---------------------------
# DISTRIBUTION
# ---------------------------

class Assignment(models.Model):
    evaluator = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['evaluator', 'project'],
                name='unique_assignment'
            )
        ]

    def clean(self):

        # Impede mais de 7 avaliadores no projeto
        project_assignments = Assignment.objects.filter(
            project=self.project
        ).exclude(id=self.id).count()

        if project_assignments >= 7:
            raise ValidationError(
                'Este projeto já possui o número máximo de avaliadores.'
            )

        # Impede avaliador de ultrapassar o limite máximo
        evaluator_assignments = Assignment.objects.filter(
            evaluator=self.evaluator
        ).exclude(id=self.id).count()

        max_projects = self.evaluator.evaluatorprofile.max_projects

        if evaluator_assignments >= max_projects:
            raise ValidationError(
                'Este avaliador já atingiu o limite máximo de projetos.'
            )

        # Impede avaliador de avaliar projeto de outro eixo
        evaluator_axis = self.evaluator.evaluatorprofile.axis
        project_axis = self.project.axis

        if evaluator_axis != project_axis:
            raise ValidationError(
                'O avaliador só pode avaliar projetos do próprio eixo.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.evaluator} - {self.project}"

# ---------------------------
# EVALUATION
# ---------------------------

class Evaluation(models.Model):
    from django.db.models import Avg
    from django.utils import timezone
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    evaluator = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    general_comment = models.TextField(blank=True)

    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['evaluator', 'project'],
                name='unique_evaluation'
            )
        ]

    def __str__(self):
        return f"Evaluation {self.id}"
    
    def calculate_final_score(self):

        average = self.score_set.aggregate(
            Avg('score')
        )['score__avg']

        self.final_score = average or 0

        super().save(update_fields=['final_score'])


    def finalize(self):

        total_criteria = Criterion.objects.count()

        total_scores = self.score_set.count()

        if total_scores < total_criteria:
            raise ValidationError(
                'A avaliação não pode ser finalizada incompleta.'
            )

        self.status = 'completed'
        self.is_finalized = True
        self.finalized_at = timezone.now()

        self.save()


# ---------------------------
# SCORES (per criterion)
# ---------------------------

class Score(models.Model):
    

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE
    )

    criterion = models.ForeignKey(
        Criterion,
        on_delete=models.CASCADE
    )

    score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )

    comment = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation', 'criterion'],
                name='unique_score_per_criterion'
            )
        ]

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        self.evaluation.calculate_final_score()

    def __str__(self):
        return f"{self.evaluation} - {self.criterion}"