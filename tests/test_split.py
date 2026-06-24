import os
from pathlib import Path
from unittest.mock import mock_open, patch

from needletail import Record, parse_fastx_file
import pytest

from commec.split import _clean_description, _write_split_fasta


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "test_data"


@pytest.fixture
def fasta_records(test_data_dir) -> dict[str, list[Record]]:
    """Fixture to parse records from multiple FASTA files into a dictionary."""
    files = [
        "multiple_records.fasta",
        "single_record.fasta",
        "has_empty_description.fasta",
    ]
    record_dict: dict[str, list[Record]] = {}
    for filename in files:
        file_path = test_data_dir / filename
        print(file_path)
        records = [r for r in parse_fastx_file(file_path)]
        print(records)
        record_dict[filename] = records
    return record_dict


@pytest.mark.parametrize(
    "description, expected",
    [
        (
            'BBa_K620001_P_22737_Coding_"WT-F87A_(p450)"',
            "BBa_K620001_P_22737_Coding_WT-F87A_p450",
        ),
        ("long description" * 20, "longdescription" * 10),
    ],
)
def test_clean_description(description, expected):
    assert _clean_description(description) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "multiple_records.fasta",
        "single_record.fasta",
    ],
)
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.join", side_effect=lambda a, b: f"{a}/{b}")
def test_write_split_fasta(
    mock_seqio_parse,
    mock_os_path_join,
    filename,
    test_data_dir,
    fasta_records,
):
    filepath = os.path.join(test_data_dir, filename)
    records = fasta_records[filename]
    mock_seqio_parse.return_value = records
    _write_split_fasta(filepath)

    # Check the correct number of output files were opened (one input + as many outputs as records)
    assert mock_open.call_count == len(records) + 1

    for record in records:
        desc = _clean_description(record.description)

        if desc:
            output_filename = f"{desc}.fasta"
        else:
            output_filename = f"{os.path.splitext(filename)[0]}-split-0.fasta"

        mock_os_path_join.assert_any_call(os.path.dirname(filepath), output_filename)
        mock_open.assert_any_call(
            os.path.join(os.path.dirname(filepath), output_filename),
            "w",
            encoding="utf-8",
        )
        mock_open().write.assert_any_call(f">{desc}{os.linesep}")
        mock_open().write.assert_any_call(f"{record.seq}")
