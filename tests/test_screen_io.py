import os
from pathlib import Path

import pytest

from commec.config.screen_io import Args, IoValidationError, ScreenIO


@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def database_dir():
    return os.path.join(os.path.dirname(__file__), "test_dbs")


@pytest.mark.parametrize(
    "fasta_name",
    [
        "single_record.fasta",
        "multiple_records.fasta",
        "has_empty_record.fasta",
        "has_empty_description.fasta",
        "has_records_with_same_description.fasta",
    ],
)
def test_default_parameters(fasta_name, test_data_dir, database_dir, tmp_path):
    input_fasta = os.path.join(test_data_dir, fasta_name)
    
    screen_io = ScreenIO(Args(
        fasta_file=input_fasta,
    ))
    assert screen_io.setup()


@pytest.mark.parametrize(
    "fasta_name,expected_record_count",
    [
        pytest.param("single_record.fasta", 1),
        pytest.param("multiple_records.fasta", 2),
    ],
)
def test_parse_input_fasta(
    fasta_name, expected_record_count, test_data_dir, database_dir, tmp_path
):
    input_fasta = os.path.join(test_data_dir, fasta_name)
    
    screen_io = ScreenIO(Args(
        database_dir=database_dir,
        fasta_file=input_fasta,
        output_prefix=tmp_path,
    ))

    queries = screen_io.parse_input_fasta()
    assert len(queries) == expected_record_count


@pytest.mark.parametrize(
    "fasta_name",
    [
        "has_empty_record.fasta",
        "has_empty_description.fasta",
        "has_records_with_same_description.fasta",
    ],
)
def test_parse_invalid_input_fasta(fasta_name, test_data_dir, database_dir, tmp_path):
    input_fasta = os.path.join(test_data_dir, fasta_name)
    
    screen_io = ScreenIO(Args(
        database_dir=database_dir,
        fasta_file=input_fasta,
        output_prefix=tmp_path,
    ))

    with pytest.raises(IoValidationError):
        screen_io.parse_input_fasta()
