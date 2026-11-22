from tictactoe.cli import main


def scripted(monkeypatch, answers):
    """Answer every input() prompt from `answers`, in order."""
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(replies))


X_WINS = ["1", "4", "2", "5", "3"]
DRAW = ["1", "2", "3", "5", "4", "6", "8", "7", "9"]


def test_a_finished_game_is_logged_with_outcome_cells_and_player(monkeypatch, tmp_path):
    log = tmp_path / "games.log"
    scripted(monkeypatch, X_WINS)
    assert main(["--two-player", "--log", str(log), "--player", "Ada"]) == 0
    assert log.read_text() == "X\t1,4,2,5,3\tAda\n"


def test_a_drawn_game_is_logged_as_a_draw(monkeypatch, tmp_path):
    log = tmp_path / "games.log"
    scripted(monkeypatch, DRAW)
    main(["--two-player", "--log", str(log)])
    assert log.read_text() == "draw\t1,2,3,5,4,6,8,7,9\t\n"


def test_a_second_game_is_appended_rather_than_replacing_the_first(monkeypatch, tmp_path):
    log = tmp_path / "games.log"
    scripted(monkeypatch, X_WINS + DRAW)
    main(["--two-player", "--log", str(log), "--player", "Ada"])
    main(["--two-player", "--log", str(log), "--player", "Ada"])
    assert log.read_text().splitlines() == [
        "X\t1,4,2,5,3\tAda",
        "draw\t1,2,3,5,4,6,8,7,9\tAda",
    ]


def test_an_abandoned_game_is_not_logged(monkeypatch, tmp_path):
    log = tmp_path / "games.log"
    scripted(monkeypatch, ["1", "q"])
    assert main(["--two-player", "--log", str(log)]) == 1
    assert not log.exists()


def test_the_log_defaults_to_a_folder_in_the_home_directory(monkeypatch, home):
    scripted(monkeypatch, X_WINS)
    main(["--two-player", "--player", "Ada"])
    assert (home / ".tictactoe" / "games.log").read_text() == "X\t1,4,2,5,3\tAda\n"


def test_a_name_with_a_line_break_stays_on_one_line(monkeypatch, tmp_path):
    log = tmp_path / "games.log"
    scripted(monkeypatch, X_WINS)
    main(["--two-player", "--log", str(log), "--player", "Ada\nO\t9\tEve"])
    assert log.read_text() == "X\t1,4,2,5,3\tAda O 9 Eve\n"


def test_logging_does_not_change_what_is_printed(monkeypatch, capsys, tmp_path):
    scripted(monkeypatch, X_WINS + X_WINS)
    main(["--two-player"])
    without = capsys.readouterr()
    main(["--two-player", "--log", str(tmp_path / "games.log"), "--player", "Ada"])
    with_options = capsys.readouterr()
    assert with_options.out == without.out
    assert with_options.err == without.err == ""


def test_a_log_that_cannot_be_written_does_not_fail_the_game(monkeypatch, capsys, tmp_path):
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("")
    scripted(monkeypatch, X_WINS)
    assert main(["--two-player", "--log", str(blocker / "games.log")]) == 0
    captured = capsys.readouterr()
    assert "X wins." in captured.out
    assert "could not write the game log" in captured.err
