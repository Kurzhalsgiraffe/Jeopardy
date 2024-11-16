var question_settings_visible = false;
        var team_settings_visible = false;
        var currently_opened_question_id;
        var is_buzzer_event_handled = false;
        var buzzer_event_stream = null;
        const question_modal = $("#question-modal")
        const add_team_form = $("#add-team-form")
        const question_cards = $(".question-card");
        const team_cards = $(".team-card");

        add_team_form.on("submit", function(event) {
            var team_name = $("#team-name-input").val().trim();
            if (team_name === "") {
                alert("Team Name cannot be empty");
                event.preventDefault();
            }
        });

        $(".modal-footer").on("click", ".answer-button-container", function() {
            const is_answer_correct = $(this).attr("data-answer") === "true";
            submitAnswer(is_answer_correct);
        });

        $(document).on('click', '.question-card', function() {
            const question_id = $(this).attr("data-question-id");
            selectQuestion(question_id);
        });

        $(document).on('click', '#toggle-question-settings-btn', function() {
            toggleQuestionSettings();
        });

        $(document).on('click', '.skip-question-btn', function(event) {
            event.stopPropagation();
            const question_id = $(this).closest(".question-card").data("question-id");
            skipQuestion(question_id)
        });

        $(document).on('click', '#toggle-team-settings-btn', function() {
            toggleTeamSettings();
        });

        $(document).on('click', '.remove-team-btn', function() {
            const team_id = $(this).closest(".team-card").data("team-id");
            removeTeam(team_id)
        });

        $(document).on('click', '.team-control-btn', function() {
            const team_id = $(this).data('team-id');
            const action = $(this).data('action');
            updateScore(team_id, action);
        });

        $(document).on('change', '.team-buzzer-id-input', function() {
            const team_id = $(this).data("team-id");
            const buzzer_id = $(this).val();
            updateBuzzerID(team_id, buzzer_id);
        });

        $(document).on('change', '.team-buzzer-sound-input', function() {
            const team_id = $(this).data("team-id");
            const buzzer_sound = $(this).val();
            playSound(`static/sounds/team_sounds/${buzzer_sound}`);
            updateTeamBuzzerSound(team_id, buzzer_sound);
        });

        $(document).on('change', '.team-active-checkbox', function() {
            const team_id = $(this).data("team-id");
            const is_checked = $(this).is(":checked");
            toggleTeamActivation(team_id, is_checked);
        });

        question_modal.on("hidden.bs.modal", function (e) {
            closeBuzzerEventStream();
            $.post("/unselect_question", function(response) {
                if (!response.success) {
                    console.error("Failed to unselect question:", response.message);
                    alert("There was an error unselecting the questions and deactivating the buzzers.");
                }
            });
        });

        function openBuzzerEventStream() {
            if (buzzer_event_stream) {
                buzzer_event_stream.close();
                buzzer_event_stream = null;
            }
            buzzer_event_stream = new EventSource('/buzzer_event_stream');

            buzzer_event_stream.onmessage = function(event) {
                const data = JSON.parse(event.data);
                $("#question-modal-answering-team").text(data.team_name + " (Buzzer " + data.buzzer_id + ")");
                if (data.buzzer_sound != null) {
                    playSound(`static/sounds/team_sounds/${data.buzzer_sound}`);
                }
            };

            buzzer_event_stream.onerror = function() {
                console.error("Error with the Quizmaster EventSource connection.");
                buzzer_event_stream.close();
                buzzer_event_stream = null; // Clean up on error
            };
        }

        function closeBuzzerEventStream() {
            if (buzzer_event_stream) {
                buzzer_event_stream.close();
                buzzer_event_stream = null;
            }
        }

        function playSound(sound_name) {
            var audio = new Audio(sound_name);
            audio.currentTime = 0;
            audio.play().catch(function(error) {
                console.error("Audio playback failed:", error);
            });
        }

        function selectQuestion(question_id) {
            currently_opened_question_id = question_id;
            const answer_button = $(".answer-button");
            const answer_text_container = $(".answer-text-container");

            $.post("/select_question/" + question_id, {}, function(data) {
                $("#question-modal-label").text(data.category + " - " + data.points + " (" + data.type + ")");
                $("#modal-question-id-span").text(data.question_id);
                $("#question-text").text(data.question);
                $("#answer-text").text(data.answer);
                $("#question-modal-answering-team").text("");

                if (data.answered_questions.some(obj => obj.hasOwnProperty(data.question_id))) {
                    answer_text_container.removeClass("blur-text");
                    answer_button.hide();

                    const answered_question = data.answered_questions.find(obj => obj.hasOwnProperty(data.question_id));
                    if (answered_question[data.question_id][0]) {
                        $("#question-modal-answering-team").text(answered_question[data.question_id][0] + " (Buzzer " + answered_question[data.question_id][1] + ")");
                    } else {
                        $("#question-modal-answering-team").text("Kein Team - Frage wurde übersprungen");
                    }
                } else {
                    answer_text_container.addClass("blur-text");
                    answer_button.show();
                    openBuzzerEventStream();
                }
                question_modal.modal("show");
            }).fail(function(jqXHR, textStatus, errorThrown) {
                alert("Error selecting question: " + errorThrown);
            });
        }

        function updateScore(team_id, action) {
            var points_input = document.getElementById("points-" + team_id);
            var points = parseInt(points_input.value);

            if (isNaN(points) || points <= 0) {
                alert("Please enter a valid number of points.");
                return;
            }

            var score_delta = action === "add" ? + points : - points;
            $.post("/update_score", { team_id: team_id, score_delta: score_delta }, function(response) {
                updateTeamScores(response);
            });
        }

        function submitAnswer(is_answer_correct) {
            $.post("/answer_question/" + currently_opened_question_id, { is_answer_correct: is_answer_correct }, function(response) {
                if (response.success) {
                    if (is_answer_correct) {
                        var card = document.querySelector(`[data-question-id="${currently_opened_question_id}"]`);
                        card.classList.add("answered");
                        card.style.opacity = "0.5";
                        question_modal.modal("hide");
                        playSound("static/sounds/game_sounds/Mario_Coin.mp3");
                    } else {
                        question_modal.modal("show");
                        openBuzzerEventStream();
                        $("#question-modal-answering-team").text("");
                        playSound("static/sounds/game_sounds/Nope.mp3");
                    }
                    updateTeamScores(response.teams);
                } else {
                    alert(response.message)
                }
            });
        }

        function skipQuestion(question_id) {
            if (confirm("Möchtest du die Frage wirklich überspringen?")) {
                var card = $(`[data-question-id="${question_id}"]`);
                if (!card.hasClass("answered")) {
                    $.post("/skip_question/" + question_id, function(response) {
                        if (response.success) {
                            card.addClass("answered").css("opacity", "0.5");
                            playSound("static/sounds/game_sounds/Windows_Error.mp3");
                        } else {
                            alert(response.message)
                        }
                    });
                }
            }
        }

        function updateTeamScores(teams) {
            teams.forEach(team => {
                const team_element = $(`[data-team-id="${team.team_id}"] .card-text`);
                if (team_element.length > 0) {
                    team_element.text(team.score);
                }
            });
        }

        function removeTeam(team_id) {
            if (confirm("Möchtest du das Team wirklich löschen?")) {
                $.post("/remove_team", { team_id: team_id }, function() {
                    location.reload();
                });
            }
        }

        function toggleTeamActivation(team_id, is_checked) {
            $.post("/toggle_team_activation", { team_id: team_id, active: is_checked }, function(response) {
                var teamCard = $(`.team-card[data-team-id="${team_id}"]`);
                if (is_checked) {
                    teamCard.addClass("active");
                } else {
                    teamCard.removeClass("active");
                }
            });
        }

        function updateBuzzerID(team_id, buzzer_id) {
            $.post("/update_buzzer_id", { team_id: team_id, buzzer_id: buzzer_id }, function(response) {
                if (response.success) {
                    response.teams.forEach(function(team) {
                        var input_element = $(`.team-buzzer-id-input[data-team-id="${team.team_id}"]`);
                        if (input_element.length) {
                            input_element.val(team.buzzer_id);
                            input_element.css("background-color", "lime");
                            setTimeout(function() {
                                input_element.css("background-color", "");
                            }, 800);
                        }
                    });
                } else {
                    alert(response.message)
                }
            });
        }

        function updateTeamBuzzerSound(team_id, buzzer_sound) {
            $.post("/update_team_buzzer_sound", { team_id: team_id, buzzer_sound: buzzer_sound }, function(response) {
                if (response.success) {
                    response.teams.forEach(function(team) {
                        var selectElement = $(`.team-buzzer-sound-input[data-team-id="${team.team_id}"]`);
                        if (selectElement.length) {
                            selectElement.val(team.buzzer_sound);
                        }
                    });
                } else {
                    alert(response.message);
                }
            });
        }

        function getTeamBuzzerSounds() {
            $.get("/get_buzzer_sounds", function(response) {
                if (response.success) {
                    response.teams.forEach(function(team) {
                        var dropdown_element = $(`.team-buzzer-sound-input[data-team-id="${team.team_id}"]`);
                        if (dropdown_element.length) {

                            dropdown_element.empty();
                            dropdown_element.append($('<option>', {
                                value: '',
                                text: 'Select Sound'
                            }));

                            response.sounds.forEach(function(sound) {
                                dropdown_element.append($('<option>', {
                                    value: sound,
                                    text: sound
                                }));
                            });
                            if (team.buzzer_sound) {
                                dropdown_element.val(team.buzzer_sound);
                            } else {
                                dropdown_element.val('');
                            }
                        }
                    });
                } else {
                    alert("Failed to load buzzer sounds: " + response.message);
                }
            });
        }

        function toggleQuestionSettings() {
            const skip_question_buttons = $(question_cards).find(".skip-question-btn");
            if (!question_settings_visible) {
                question_settings_visible = true;
                skip_question_buttons.show();
            } else {
                question_settings_visible = false;
                skip_question_buttons.hide();
            }
        }

        function toggleTeamSettings() {
            const team_card_settings = $(team_cards).find(".team-card-settings");
            const remove_team_buttons = $(team_cards).find(".remove-team-btn");

            if (!team_settings_visible) {
                team_settings_visible = true;
                add_team_form.show();
                remove_team_buttons.show();
                team_card_settings.show();
                team_cards.show();
            } else {
                team_settings_visible = false;
                add_team_form.hide();
                remove_team_buttons.hide();
                team_card_settings.hide();
                $(".team-card:not(.active)").hide();
            }
        }

        $(document).ready(function() {
            const team_card_settings = $(team_cards).find(".team-card-settings");
            const skip_question_buttons = $(question_cards).find(".skip-question-btn");
            const remove_team_buttons = $(team_cards).find(".remove-team-btn");
            add_team_form.hide();
            remove_team_buttons.hide();
            skip_question_buttons.hide();
            team_card_settings.hide();
            $(".team-card:not(.active)").hide();
            getTeamBuzzerSounds();
        });