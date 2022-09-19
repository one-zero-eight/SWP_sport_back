const session_id = window.location.href.split('/').pop();

let students_in_table = {};
let exercises_global = [];

function load_session() {
	if (session_id !== 'new') {
		fetch(`/api/fitnesstest/sessions/${session_id}`, {
			method: 'GET',
			'X-CSRFToken': csrf_token,
		})
			.then((response) => {
				return response.json();
			})
			.then((data) => {
                let session = data['session'];
                let results = data['results'];
                let exercises = data['exercises'];
				let retake = session['retake'];

                // insert info about session
                $('#session-info-semester').html(session['semester']['name']);
                $('#session-info-date').html(new Date(session['date']).toLocaleString('en-GB'));
                $('#session-info-teacher').html(session['teacher']);
				// load info about retake
				$('#fitness-test-retake-check').attr('disabled', 'disabled');
				if (retake) {
					$('#fitness-test-retake-check').attr('checked', 'checked');
				}

                // construct tabs and tables for each exercise, fill the tables
                construct_exercises(exercises);
                fill_exercises_with_results(exercises, results);
            })
			.catch(function (err) {
				console.log(err);
        });
	}
    else {
        fetch('/api/fitnesstest/exercises', {
            method: 'GET',
            'X-CSRFToken': csrf_token,
        })
            .then((response) => {
                return response.json();
            })
            .then((exercises) => {
                construct_exercises(exercises);
            });
    }
}
function construct_exercises(exercises) {
    exercises.forEach((exercise, index) => {
        exercises_global.push(exercise);
        // build tabs with exercises
        let ex_tab_li = document.createElement('li');
        ex_tab_li.classList.add('nav-item');

        let ex_tab_a = document.createElement('a');
        ex_tab_a.classList.add('nav-link');
        ex_tab_a.innerHTML = exercise.name;
        ex_tab_a.setAttribute('href', `#ex-${exercise.id}`);
        ex_tab_a.setAttribute('data-toggle', 'tab');

        ex_tab_li.appendChild(ex_tab_a);
        document.getElementById('exercise-tabs').appendChild(ex_tab_li);

        let div_table = document.createElement('div');
        div_table.id = `ex-${exercise.id}`;
        div_table.classList.add('tab-pane', 'fade', 'table-responsive');

        // make first exercise active
        if (index === 0) {
            ex_tab_a.classList.add('active');
            div_table.classList.add('show', 'active');
        }
        // build table for exercise
        const student_ex_table = $('<table class="table w-100">');
        student_ex_table
            .append('<thead />')
            .children('thead')
            .append('<tr />')
            .children('tr')
            .append(`<th scope="col">Student</th><th scope="col">${exercise.name} — result</th>`);
        student_ex_table.append(`<tbody id="ex-table-${exercise.id}">`);

        div_table.appendChild(student_ex_table[0]);
        document.getElementById('student-exercise-table').appendChild(div_table);
    });
}

function fill_exercises_with_results(exercises, results) {
    // fill the table with students' results
    exercises.forEach((exercise) => {
        let student_results = results[exercise.id];
        student_results.forEach((student_result) => {
            add_student_row_for_exercise(exercise, student_result.student);

            if (exercise.select) {
                $(`#ex_${exercise.id}_select option[value=${student_result.value}]`)
                    .attr('selected', 'selected');
            } else {
                if (exercise.unit === 'second(s)') {
                    $(`#ex_${exercise.id}_value`)
                        .attr('value', `${
                            new Date(student_result.value * 1000).toISOString().substring(14, 19)
                        }`);
                }
                else {
                    $(`#ex_${exercise.id}_value`)
                        .attr('value', `${student_result.value}`);
                }
            }
        });
    });
}

// Adds single row at particular exercise
function add_student_row_for_exercise(exercise, student) {
	$('#ft-session-save').removeAttr('disabled');
	let row = `<tr id="student_${student.id}_${exercise.id}">
                <td>${student.name}
                    ${
                        student.medical_group === 'Special 1'
                            ? `<span class="badge badge-pill badge-danger text-uppercase">
                                ${student.medical_group}
                               </span>`
                            : ''
                    }
               </td>`;
	if (exercise.select) {
        row += `<td style="cursor: pointer">
                    <select class="custom-select" id="ex_${exercise.id}_select">
                        <option selected disabled value="-1">Choose...</option>
                    </select>
                </td>
            </tr>`;
        $(`#ex-table-${exercise.id}`).prepend($(row));

        exercise.select.forEach((option, index) => {
            $(`#ex_${exercise.id}_select`).first()
                .append(
                    $('<option/>', {
                        'value': `${index}`,
                        text: option
                    })
                );
        });
	} else {
        row += `<td style="cursor: pointer">
                    <div class="input-group" onsubmit="return false;">
                        <input class="form-control" id="ex_${exercise.id}_value"
                            ${
                                exercise.unit === 'second(s)'
                                    ? 'type="text" value="" placeholder="00:00"'
                                    : 'type="number" min="0" value="0"'
                            }
							step="1"/>
                            ${
                                (exercise.unit && exercise.unit !== 'second(s)')
                                    ? `<div class="input-group-append">
                                        <span class="input-group-text">${exercise.unit}</span>
                                       </div>`
                                    : ''
                            }
                    </div>
                </td>
            </tr>`;
        $(`#ex-table-${exercise.id}`).prepend($(row));
        if (exercise.unit === 'second(s)') {
            $.mask.definitions['S']='[0-5]';
            $(`#ex_${exercise.id}_value`).mask("99:S9");
        }
	}
	students_in_table[student.id] = 1;
}
// Adds multiple rows i.e., at each exercise
function add_new_student_rows(student) {
	$('#ft-session-save').removeAttr('disabled');
	exercises_global.forEach((exercise) => {
        add_student_row_for_exercise(exercise, student);
    });
}

let current_student;

function parse_student_from_server(data) {
	const [student_id, student_name, student_email, student_medical_group, student_gender] = data.split('_');
	current_student = parseInt(student_id);
	const student_row = students_in_table[student_id];
	if (student_row == null) {
		// check if current student is in the table
		if (student_gender === '-1') {
			$('#gender-modal-name').text(student_name);
			$('#gender-modal').modal('show');
		}
        add_new_student_rows(
            {id: student_id,
            name: student_name,
            email: student_email,
            medical_group: student_medical_group}
        ); // add if student isn't present
	} else {
		// student_row[0].scrollIntoView(); // scroll to the row with student
		// student_row.delay(25).fadeOut().fadeIn().fadeOut().fadeIn();
	}
}

function autocomplete_select(event, ui) {
	event.preventDefault(); // prevent adding the value into the text field
	event.stopPropagation(); // stop other handlers from execution
	$(this).val(''); // clear the input field
	parse_student_from_server(ui.item.value);
}

$(function () {
	$('#student_emails')
		.autocomplete({
			source: function (request, response) {
				$.ajax({
					url: '/api/fitnesstest/suggest_student',
					data: { term: request.term },
					dataType: 'json',
					success: response,
					error: () => response([]),
				});
			},
			select: autocomplete_select,
		})
		.autocomplete('option', 'appendTo', '.student_email_suggestor');
	$('[data-toggle="tooltip"]').tooltip();
});

function save_table() {
	const student_ids = Object.keys(students_in_table);
	let result = [];
	let cant_submit = false;
	for (let i = 0; i < exercises_global.length; i++) {
		if (student_ids.length === 0) {
			cant_submit = true;
			break;
		}
        let exercise = exercises_global[i];
		student_ids.forEach((sid) => {
			let val;
			let inp_field = document
				.getElementById(`student_${sid}_${exercise.id}`)
				.getElementsByTagName('input')[0];
			let sel_field = document
				.getElementById(`student_${sid}_${exercise.id}`)
				.getElementsByTagName('select')[0];
			if (inp_field) {
				if (exercise.unit === 'second(s)') {
					val = inp_field.value.split(':').reduce((acc, time) => (60 * acc) + +time);
				} else {
					val = inp_field.value;
				}
			} else {
				val = sel_field.value;
			}
			if (val === '') {
				toastr.error(
					`There are no values for some students in <b>${exercise.name} exercise</b>`,
					'Value error'
				);
				cant_submit = true;
			} else if (parseInt(val) < 0) {
				toastr.error(
					`Values should be <b>positive</b> or you have not selected the option. Check <b>${exercise.name} exercise</b>`,
					'Value error'
				);
				cant_submit = true;
			}
			result.push({
                student_id: sid,
                exercise_id: exercise.id,
                value: val });
		});
	}
	let body = {
		retake: $('#fitness-test-retake-check').is(':checked'),
		results: result,
	}
	if (cant_submit) {
		return;
	}
	if (session_id === 'new') {
		fetch('/api/fitnesstest/upload', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrf_token,
			},
			body: JSON.stringify(body),
		})
			.then((response) => {
				if (response.ok) {
					return response.json();
				}
				throw new Error('Something went wrong.');
			})
			.then((response) => {
				$('#ft-session-save').attr('disabled', '');
				toastr.success(
					'The fitness test has been successfuly saved',
					'Saved',
					1500
				);
				setTimeout(() => {
					window.location.href = `/fitness_test/${response['session_id']}`;
				}, 1500);
			})
			.catch(function (error) {
				toastr.error(`${error}`, 'Server error');
			});
	} else {
		fetch(`/api/fitnesstest/upload/${session_id}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrf_token,
			},
			body: JSON.stringify(body),
		})
			.then((response) => {
				if (response.ok) {
					return response.json();
				}
				throw new Error('Something went wrong.');
			})
			.then(() => {
				toastr.success(
					'The fitness test has been successfuly saved',
					'Saved',
					1500
				);
			})
			.catch(function (error) {
				toastr.error(`${error}`, 'Server error');
			});
	}
}

function save_gender(val) {
	fetch('/api/profile/change_gender', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': csrf_token,
		},
		body: JSON.stringify({ student_id: current_student, gender: val }),
	})
		.then((response) => {
			if (response.ok) {
				return response.text();
			}
			throw new Error('Something went wrong.');
		})
		.then(() => {
			toastr.success('The gender has been successfuly set', 'Set', 1000);
			$('#gender-modal').modal('hide');
		})
		.catch(function (error) {
			toastr.error(`${error}`, 'Server error');
		});
}

load_session();
