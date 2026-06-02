"""Tests for standalone CLI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from visualizer.standalone import _default_board_id, _default_serial, build_arg_parser, run_standalone


def test_defaults() -> None:
    assert isinstance(_default_board_id(), int)
    assert _default_serial()


def test_parser() -> None:
    args = build_arg_parser().parse_args([])
    assert args.n_channels == 8


@patch("visualizer.standalone.get_visualizer_settings")
def test_run_standalone_missing_config(mock_settings: MagicMock) -> None:
    from visualizer.config.exceptions import VisualizerConfigError

    mock_settings.side_effect = VisualizerConfigError("missing")
    assert run_standalone([]) == 1


@patch("visualizer.standalone.time.sleep", side_effect=KeyboardInterrupt)
@patch("visualizer.standalone.BoardStreamFeeder")
@patch("visualizer.standalone.EEGVisualizer")
@patch("brainflow.board_shim.BoardShim")
@patch("visualizer.standalone.get_visualizer_settings")
def test_run_standalone_happy_path(
    mock_settings: MagicMock,
    mock_board_cls: MagicMock,
    mock_vis_cls: MagicMock,
    mock_feeder_cls: MagicMock,
    _sleep: MagicMock,
    visualizer_env: None,
) -> None:
    from visualizer.config.settings import VisualizerSettings

    mock_settings.return_value = VisualizerSettings(
        window_sec=5,
        plot_hz=20,
        amplitude_uv=100,
    )
    board = MagicMock()
    board.is_prepared.return_value = True
    mock_board_cls.return_value = board

    vis = MagicMock()
    vis.is_running = True
    mock_vis_cls.return_value = vis
    feeder = MagicMock()
    mock_feeder_cls.return_value = feeder

    assert run_standalone(["--board-id", "8"]) == 0
    board.prepare_session.assert_called_once()
    vis.start.assert_called_once()
    feeder.stop.assert_called_once()


@patch("brainflow.board_shim.BoardShim")
@patch("visualizer.standalone.get_visualizer_settings")
def test_run_standalone_prepare_fails(
    mock_settings: MagicMock,
    mock_board_cls: MagicMock,
    visualizer_env: None,
) -> None:
    from visualizer.config.settings import VisualizerSettings

    mock_settings.return_value = VisualizerSettings(
        window_sec=5,
        plot_hz=20,
        amplitude_uv=100,
    )
    board = MagicMock()
    board.prepare_session.side_effect = RuntimeError("no device")
    mock_board_cls.return_value = board

    assert run_standalone([]) == 1


@patch("visualizer.standalone.time.sleep", side_effect=KeyboardInterrupt)
@patch("visualizer.standalone.BoardStreamFeeder")
@patch("visualizer.standalone.EEGVisualizer")
@patch("brainflow.board_shim.BoardShim")
@patch("visualizer.standalone.get_visualizer_settings")
def test_run_standalone_cleanup_errors(
    mock_settings: MagicMock,
    mock_board_cls: MagicMock,
    mock_vis_cls: MagicMock,
    mock_feeder_cls: MagicMock,
    _sleep: MagicMock,
    visualizer_env: None,
) -> None:
    from visualizer.config.settings import VisualizerSettings

    mock_settings.return_value = VisualizerSettings(
        window_sec=5,
        plot_hz=20,
        amplitude_uv=100,
    )
    board = MagicMock()
    board.is_prepared.return_value = True
    board.stop_stream.side_effect = RuntimeError("disconnect")
    mock_board_cls.return_value = board
    vis = MagicMock()
    vis.is_running = True
    mock_vis_cls.return_value = vis
    mock_feeder_cls.return_value = MagicMock()

    assert run_standalone([]) == 0


@patch("visualizer.standalone.time.sleep", side_effect=KeyboardInterrupt)
@patch("visualizer.standalone.BoardStreamFeeder")
@patch("visualizer.standalone.EEGVisualizer")
@patch("brainflow.board_shim.BoardShim")
@patch("visualizer.standalone.get_visualizer_settings")
def test_run_standalone_exits_when_visualizer_not_running(
    mock_settings: MagicMock,
    mock_board_cls: MagicMock,
    mock_vis_cls: MagicMock,
    mock_feeder_cls: MagicMock,
    _sleep: MagicMock,
    visualizer_env: None,
) -> None:
    from visualizer.config.settings import VisualizerSettings

    mock_settings.return_value = VisualizerSettings(
        window_sec=5,
        plot_hz=20,
        amplitude_uv=100,
    )
    board = MagicMock()
    board.is_prepared.return_value = False
    mock_board_cls.return_value = board
    vis = MagicMock()
    vis.is_running = False
    mock_vis_cls.return_value = vis
    mock_feeder_cls.return_value = MagicMock()

    assert run_standalone([]) == 0
    board.stop_stream.assert_not_called()
