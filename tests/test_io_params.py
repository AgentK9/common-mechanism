import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from commec.config.screen_io import Args, ScreenIO

INPUT_QUERY = Path(__file__).parent / "test_data" / "single_record.fasta"
DATABASE_DIRECTORY = Path(__file__).parent / "test_dbs"


@pytest.fixture
def expected_defaults():
    return {
        "base_paths": {"default": "commec-dbs/"},
        "databases": {
            "low_concern": {
                "rna": {"path": "commec-dbs/low_concern/rna/low_concern.cm"},
                "dna": {"path": "commec-dbs/low_concern/dna/low_concern.fasta"},
                "protein": {"path": "commec-dbs/low_concern/protein/low_concern.hmm"},
                "annotations": "commec-dbs/low_concern/low_concern_annotations.tsv",
                "taxids": "commec-dbs/low_concern/vax_taxids.txt",
            },
            "biorisk": {
                "path": "commec-dbs/biorisk/biorisk.hmm",
                "annotations": "commec-dbs/biorisk/biorisk_annotations.csv",
                "taxids": "commec-dbs/biorisk/reg_taxids.txt",
            },
            "regulated_nt": {"path": "commec-dbs/nt_blast/core_nt"},
            "regulated_protein": {
                "blast": {"path": "commec-dbs/nr_blast/nr"},
                "diamond": {"path": "commec-dbs/nr_dmnd/nr.dmnd"},
            },
            "taxonomy": {
                "path": "commec-dbs/taxonomy/",
            },
        },
        "threads": 1,
        "protein_search_tool": "blastx",
        "skip_taxonomy_search": False,
        "skip_nt_search": False,
        "do_cleanup": False,
        "diamond_jobs": None,
        "force": False,
        "resume": False,
        "verbose": False,
    }


@pytest.fixture
def custom_yaml_config():
    return {
        "databases": {"biorisk": {"taxids": "custom_path.txt"}},
        "skip_taxonomy_search": True,
        "force": True,
        "threads": 8,
    }


@pytest.fixture
def expected_updated_from_custom_yaml():
    return {
        "base_paths": {"default": "commec-dbs/"},
        "databases": {
            "low_concern": {
                "rna": {"path": "commec-dbs/low_concern/rna/low_concern.cm"},
                "dna": {"path": "commec-dbs/low_concern/dna/low_concern.fasta"},
                "protein": {"path": "commec-dbs/low_concern/protein/low_concern.hmm"},
                "annotations": "commec-dbs/low_concern/low_concern_annotations.tsv",
                "taxids": "commec-dbs/low_concern/vax_taxids.txt",
            },
            "biorisk": {
                "path": "commec-dbs/biorisk/biorisk.hmm",
                "annotations": "commec-dbs/biorisk/biorisk_annotations.csv",
                "taxids": "custom_path.txt",
            },
            "regulated_nt": {"path": "commec-dbs/nt_blast/core_nt"},
            "regulated_protein": {
                "blast": {"path": "commec-dbs/nr_blast/nr"},
                "diamond": {"path": "commec-dbs/nr_dmnd/nr.dmnd"},
            },
            "taxonomy": {
                "path": "commec-dbs/taxonomy/",
            },
        },
        "threads": 8,
        "protein_search_tool": "blastx",
        "skip_taxonomy_search": True,
        "skip_nt_search": False,
        "do_cleanup": False,
        "diamond_jobs": None,
        "force": True,
        "resume": False,
        "verbose": False,
    }


def test_missing_input_file():
    # TODO?
    with pytest.raises(SystemExit):
        args = Args(
            verbose=False,
            database_dir=Path(),
            fasta_file=Path(),
            output_prefix=Path(),
            config_yaml=None,
            user_specified_args={},
        )


def test_default_config_only(expected_defaults):
    """Test that default config is loaded when no overrides exist"""
    params = ScreenIO(Args(
        verbose=False,
        database_dir=Path(),
        fasta_file=Path(),
        output_prefix=Path(),
        config_yaml=None,
        user_specified_args={},
    ))

    assert expected_defaults == params.config


def test_user_yaml_override(
    tmp_path, expected_updated_from_custom_yaml, custom_yaml_config
):
    """Test that user YAML properly overrides default config"""
    # Create user config
    user_config_path = tmp_path / "user_config.yaml"
    with open(user_config_path, "w") as f:
        yaml.dump(custom_yaml_config, f)

    params = ScreenIO(Args(
        fasta_file=Path(INPUT_QUERY),
        database_dir=Path(DATABASE_DIRECTORY),
        config_yaml=user_config_path
    ))

    # Check that user YAML values override defaults
    assert expected_updated_from_custom_yaml == params.config


def test_cli_override(tmp_path, expected_updated_from_custom_yaml, custom_yaml_config):
    """Test that CLI args properly override both YAML configs"""
    # Create user config
    user_config_path = tmp_path / "user_config.yaml"
    with open(user_config_path, "w") as f:
        yaml.dump(custom_yaml_config, f)

    # Add CLI args
    cli_args = [
        INPUT_QUERY,
        "--config",
        str(user_config_path),
        "--skip-tx",  # skip taxonomy
        "--skip-nt",  # skip nt search
        "-c",  # do_cleanup
        "-d",
        str(tmp_path),
    ]

    params = ScreenIO(Args(
        fasta_file=INPUT_QUERY,
        config_yaml=user_config_path,
        database_dir=tmp_path,
        
    ))

    # Override defaults with user YAML
    expected_updated_from_custom_yaml["skip_nt_search"] = True
    expected_updated_from_custom_yaml["do_cleanup"] = True
    db_str_to_override = expected_updated_from_custom_yaml["base_paths"]["default"]

    def recursive_override(dictionary, str_to_override, override_str):
        """
        Recursively apply string formatting to read paths from nested yaml config dicts.
        """
        if isinstance(dictionary, dict):
            return {
                key: recursive_override(value, str_to_override, override_str)
                for key, value in dictionary.items()
            }
        if isinstance(dictionary, str):
            return dictionary.replace(str_to_override, override_str)
        return dictionary

    expected_defaults = recursive_override(
        expected_updated_from_custom_yaml, db_str_to_override, str(tmp_path) + "/"
    )

    assert expected_defaults == params.config


def test_missing_default_config():
    """Test that missing default config raises appropriate error"""
    with patch("importlib.resources.files") as mock_files:
        mock_files.return_value.joinpath.return_value.exists.return_value = False

        with pytest.raises(FileNotFoundError, match="No default yaml found"):
            _ = ScreenIO(Args(
                fasta_file=INPUT_QUERY
            ))


@pytest.mark.parametrize(
    "base_path, low_concern_path, expected_path",
    [
        # Expected (basepath has terminal separator)
        (
            "commec-test/",
            "{default}low_concern/rna/test.cm",
            "commec-test/low_concern/rna/test.cm",
        ),
        # No separators
        (
            "commec-test",
            "{default}low_concern/rna/test.cm",
            "commec-test/low_concern/rna/test.cm",
        ),
        # Subpath has separator
        (
            "commec-test",
            "{default}/low_concern/rna/test.cm",
            "commec-test//low_concern/rna/test.cm",
        ),
        # Double separators
        (
            "commec-test/",
            "{default}/low_concern/rna/test.cm",
            "commec-test//low_concern/rna/test.cm",
        ),
    ],
)
def test_format_config_paths(tmp_path, base_path, low_concern_path, expected_path):
    config_yaml = {
        "base_paths": {"default": base_path},
        "databases": {"low_concern": {"rna": {"path": low_concern_path}}},
    }
    user_config_path = tmp_path / "user_config.yaml"
    with open(user_config_path, "w") as f:
        yaml.dump(config_yaml, f)

    params = ScreenIO(Args(
        fasta_file=INPUT_QUERY,
        config_yaml=user_config_path,
    ))

    assert expected_path == params.config["databases"]["low_concern"]["rna"]["path"]


@pytest.mark.parametrize(
    "input_file, prefix_arg, expected_prefix, is_makedirs_called",
    [
        # No prefix - keeps relative path
        ("dir/file.fasta", None, "dir/file", False),
        # Directory prefix - places in dir
        ("./file.fasta", "dir/output/", "dir/output/file", True),
        # Custom prefix - use that directly
        ("dir/file.fasta", "dir/output", "dir/output", False),
        # User directory prefix - places in expanded dir
        ("dir/file.fasta", "~", "~/file", True),
        # Relative directory prefix - places in dir
        ("dir/file.fasta", "..", "../file", True),
    ],
)
@patch("os.makedirs")
def test_get_output_prefix(
    mock_makedirs, input_file, prefix_arg, expected_prefix, is_makedirs_called
):
    prefix, output_prefix, input_prefix = ScreenIO._get_output_prefixes(
        input_file, prefix_arg
    )
    assert expected_prefix == prefix, f"Expected: {expected_prefix}, got {prefix}"

    # Verify makedirs was called when appropriate
    # if is_makedirs_called:
    #    mock_makedirs.assert_called_once_with(expand_and_normalize(prefix_arg), exist_ok=True)
    # else:
    #    mock_makedirs.assert_not_called()
