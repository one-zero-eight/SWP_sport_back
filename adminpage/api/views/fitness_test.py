from collections import defaultdict

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.permissions import (
    IsTrainer, IsStudent,
)
from api.serializers import (
    FitnessTestResults,
    NotFoundSerializer,
    ErrorSerializer, SuggestionSerializer
)

from api.crud import get_exercises_crud, post_student_exercises_result_crud, \
    get_email_name_like_students, get_ongoing_semester, get_score, get_max_score
from api.serializers.attendance import SuggestionQueryFTSerializer
from api.serializers.fitness_test import FitnessTestExerciseSerializer, FitnessTestSessionSerializer, \
    FitnessTestSessionWithResult, FitnessTestStudentResult
from api.serializers.semester import SemesterInSerializer
from sport.models import FitnessTestSession, FitnessTestResult, FitnessTestExercise, Semester


@swagger_auto_schema(
    method="GET",
    operation_description='Get all exercises by `semester_id`. If `semester_id` is not set, returns current semester '
                          'exercises.',
    query_serializer=SemesterInSerializer(),
    responses={
        status.HTTP_200_OK: FitnessTestExerciseSerializer(many=True),
    }
)
@api_view(["GET"])
def get_exercises(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get('semester_id')

    if semester_id is None:
        semester_id = get_ongoing_semester()
    exercises = get_exercises_crud(semester_id)

    return Response(FitnessTestExerciseSerializer(exercises, many=True).data)


@swagger_auto_schema(
    method="GET",
    operation_description='Get all sessions by `semester_id`. If `semester_id` is not set, returns all sessions.',
    query_serializer=SemesterInSerializer(),
    responses={
        status.HTTP_200_OK: FitnessTestSessionSerializer(many=True)
    }
)
@api_view(["GET"])
def get_sessions(request, **kwargs):
    serializer = SemesterInSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    semester_id = serializer.validated_data.get('semester_id')

    if semester_id is None:
        sessions = FitnessTestSession.objects.all()
    else:
        sessions = FitnessTestSession.objects.filter(semester_id=semester_id)

    return Response(FitnessTestSessionSerializer(sessions, many=True).data)


@swagger_auto_schema(
    method="GET",
    responses={
        status.HTTP_200_OK: FitnessTestStudentResult(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsStudent])
def get_result(request, **kwargs):
    results = FitnessTestResult.objects.filter(student_id=request.user.student.user_id)
    if not len(results):
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = []
    for result_distinct_semester in results.values('exercise__semester_id').distinct():
        semester_id = result_distinct_semester['exercise__semester_id']
        semester = Semester.objects.get(id=semester_id)

        total_score = 0
        result_list = []
        for result in results.filter(exercise__semester_id=semester_id):
            result_list.append({
                'exercise': result.exercise.exercise_name,
                'unit': result.exercise.value_unit,
                'value': (result.value
                          if result.exercise.select is None
                          else result.exercise.select.split(',')[result.value]),
                'score': get_score(request.user.student, result),
                'max_score': get_max_score(request.user.student, result),
            })
            grade = result_list[-1]['score'] >= result.exercise.threshold
            total_score += result_list[-1]['score']

        grade = grade and total_score >= semester.points_fitness_test
        data.append({
            'semester': semester.name,
            'grade': grade,
            'total_score': total_score,
            'details': result_list,
        })

    return Response(data=data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="GET",
    responses={
        status.HTTP_200_OK: FitnessTestSessionWithResult()
    }
)
@api_view(["GET"])
def get_session_info(request, session_id, **kwargs):
    results_dict = defaultdict(list)
    for result in FitnessTestResult.objects.filter(session_id=session_id):
        results_dict[result.exercise.id].append(result)

    return Response(FitnessTestSessionWithResult({
        'session': FitnessTestSession.objects.get(id=session_id),
        'exercises': FitnessTestExercise.objects.filter(
            id__in=FitnessTestResult.objects.filter(session_id=session_id).values_list('exercise').distinct()
        ),
        'results': results_dict
    }).data)


@swagger_auto_schema(
    method="POST",
    request_body=FitnessTestResults,
    responses={
        status.HTTP_404_NOT_FOUND: NotFoundSerializer,
        status.HTTP_400_BAD_REQUEST: ErrorSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsTrainer])
def post_student_exercises_result(request, session_id=None, **kwargs):
    trainer = request.user
    if not trainer.has_perm('sport.change_fitness_test'):
        return Response(
            status=400,
        )
    serializer = FitnessTestResults(data=request.data)
    serializer.is_valid(raise_exception=True)
    exercises = serializer.validated_data['result']
    session = post_student_exercises_result_crud(exercises, session_id, request.user)
    return Response({'session_id': session})


# TODO: Rewrite suggest to JSON
@swagger_auto_schema(
    method="GET",
    query_serializer=SuggestionQueryFTSerializer,
    responses={
        status.HTTP_200_OK: SuggestionSerializer(many=True),
    }
)
@api_view(["GET"])
@permission_classes([IsTrainer])
def suggest_fitness_test_student(request, **kwargs):
    serializer = SuggestionQueryFTSerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)

    suggested_students = get_email_name_like_students(
        serializer.validated_data["term"],
        requirement=(~Q(fitnesstestresult__exercise__semester=get_ongoing_semester()))
    )
    return Response([
        {
            "value": f"{student['id']}_"
                     f"{student['full_name']}_"
                     f"{student['email']}_"
                     f"{student['medical_group__name']}_"
                     f"{student['gender']}",
            "label": f"{student['full_name']} "
                     f"({student['email']})",
        }
        for student in suggested_students
    ])
