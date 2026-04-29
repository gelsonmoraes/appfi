from .models import EvaluatorProfile
from django.contrib import admin
from .models import (
    Axis,
    SystemConfig,
    Project,
    Criterion,
    Assignment,
    Evaluation,
    Score
)


@admin.register(Axis)
class AxisAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date')


@admin.register(EvaluatorProfile)
class EvaluatorProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'axis')
    list_filter = ('axis',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'student_name', 'school', 'grade', 'axis')
    list_filter = ('axis',)
    search_fields = ('title', 'student_name', 'school')


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'is_highlight')
    list_filter = ('category', 'is_highlight')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluator', 'project', 'created_at')
    list_filter = ('evaluator',)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluator', 'project', 'status', 'final_score', 'is_finalized')
    list_filter = ('status', 'is_finalized')
    search_fields = ('project__title', 'evaluator__username')


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluation', 'criterion', 'score')
    list_filter = ('criterion',)
    
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


class EvaluatorProfileInline(admin.StackedInline):
    model = EvaluatorProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = (EvaluatorProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)