import datetime

from sport.models import FitnessTestResult, FitnessTestExercise, FitnessTestGrading, Student, FitnessTestSession
from api.crud import get_ongoing_semester


def get_all_exercises():
    return list(FitnessTestGrading.objects.filter(semester=get_ongoing_semester()))


def post_student_exercises_result_crud(results, session_id, teacher):
    session, created = FitnessTestSession.objects.get_or_create(id=session_id, defaults={'teacher_id': teacher.id, 'date': datetime.datetime.now()})
    # print(session)
    for res in results:
        student = Student.objects.get(user__id=res['student_id'])
        exercise = FitnessTestExercise.objects.get(
            exercise_name=res['exercise_name'])
        FitnessTestResult.objects.update_or_create(exercise=exercise, semester=get_ongoing_semester(),
                                                   student=student, defaults={'value': res['value']}, session=session)
    return session.id


def get_student_score(student: Student):
    score = 0
    results = FitnessTestResult.objects.filter(
        student=student, semester=get_ongoing_semester())
    for result in results:
        score += FitnessTestGrading.objects.get(exercise=result.exercise, semester=get_ongoing_semester(),
                                                start_range__lt=result.value, end_range__gte=result.value).score
    if score < get_ongoing_semester().points_fitness_test:
        return {"score": score, "result": 0}
    else:
        return {"score": score, "result": 1}