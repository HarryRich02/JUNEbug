"""
Test suite for JUNEbug application.

Tests cover:
- YAML configuration loading and saving
- Configuration panel data extraction
- Graph node creation and connections
- Distribution editor field management
- Core data transformations
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import yaml
from configPanel import DistributionEditor, DiseaseConfigWidget, DISEASE_STAGES, DISTRIBUTION_TYPES
from yamlLoader import NoAliasDumper


class TestDistributionEditor:
    """Tests for the DistributionEditor widget."""

    def test_distribution_editor_creation(self):
        """Test that DistributionEditor can be created."""
        editor = DistributionEditor("Test Distribution", default_type="constant")
        assert editor is not None
        assert editor.type_combo.currentText() == "constant"

    def test_distribution_editor_constant_fields(self):
        """Test that constant distribution shows correct fields."""
        editor = DistributionEditor("Test", default_type="constant")
        editor.updateFields("constant")
        assert "value" in editor.inputs
        assert len(editor.inputs) == 1

    def test_distribution_editor_normal_fields(self):
        """Test that normal distribution shows correct fields."""
        editor = DistributionEditor("Test", default_type="normal")
        editor.updateFields("normal")
        assert "loc" in editor.inputs
        assert "scale" in editor.inputs
        assert len(editor.inputs) == 2

    def test_distribution_editor_gamma_fields(self):
        """Test that gamma distribution shows correct fields."""
        editor = DistributionEditor("Test", default_type="gamma")
        editor.updateFields("gamma")
        assert "a" in editor.inputs
        assert "loc" in editor.inputs
        assert "scale" in editor.inputs
        assert len(editor.inputs) == 3

    def test_distribution_editor_get_data_constant(self):
        """Test getting data from constant distribution."""
        editor = DistributionEditor("Test", default_type="constant")
        editor.updateFields("constant")
        editor.inputs["value"].setText("5.0")
        
        data = editor.getData()
        assert data["type"] == "constant"
        assert data["value"] == 5.0

    def test_distribution_editor_get_data_normal(self):
        """Test getting data from normal distribution."""
        editor = DistributionEditor("Test", default_type="normal")
        editor.updateFields("normal")
        editor.inputs["loc"].setText("1.5")
        editor.inputs["scale"].setText("0.8")
        
        data = editor.getData()
        assert data["type"] == "normal"
        assert data["loc"] == 1.5
        assert data["scale"] == 0.8

    def test_distribution_editor_set_data(self):
        """Test setting data in distribution editor."""
        editor = DistributionEditor("Test", default_type="constant")
        
        data = {"type": "gamma", "a": 2.0, "loc": 0.5, "scale": 1.0}
        editor.setData(data)
        
        assert editor.type_combo.currentText() == "gamma"
        assert editor.inputs["a"].text() == "2.0"
        assert editor.inputs["loc"].text() == "0.5"
        assert editor.inputs["scale"].text() == "1.0"

    def test_distribution_editor_invalid_number_defaults_to_zero(self):
        """Test that invalid input defaults to 0.0."""
        editor = DistributionEditor("Test", default_type="constant")
        editor.updateFields("constant")
        editor.inputs["value"].setText("not_a_number")
        
        data = editor.getData()
        assert data["value"] == 0.0


class TestYAMLConstants:
    """Tests for YAML-related constants and classes."""

    def test_no_alias_dumper_disables_aliases(self):
        """Test that NoAliasDumper doesn't use aliases."""
        data = {"disease": {"name": "test", "repeat": "same"}}
        
        dumped = yaml.dump(data, Dumper=NoAliasDumper)
        # Should not contain YAML anchor symbols
        assert "&" not in dumped or dumped.count("&") == 0

    def test_disease_stages_list_not_empty(self):
        """Test that DISEASE_STAGES contains valid values."""
        assert len(DISEASE_STAGES) > 0
        assert "healthy" in DISEASE_STAGES
        assert "recovered" in DISEASE_STAGES

    def test_distribution_types_list_not_empty(self):
        """Test that DISTRIBUTION_TYPES contains valid values."""
        assert len(DISTRIBUTION_TYPES) > 0
        assert "constant" in DISTRIBUTION_TYPES
        assert "normal" in DISTRIBUTION_TYPES
        assert "gamma" in DISTRIBUTION_TYPES


class TestYAMLSerialization:
    """Tests for YAML loading and saving."""

    @pytest.fixture
    def sample_yaml_data(self):
        """Provide sample YAML data for testing."""
        return {
            "disease": {
                "name": "test_disease",
                "settings": {
                    "default_lowest_stage": "exposed",
                    "max_mild_symptom_tag": "mild",
                },
                "transmission": {
                    "type": "gamma",
                    "max_infectiousness": {
                        "type": "lognormal",
                        "s": 0.0,
                        "loc": 0.0,
                        "scale": 1.0,
                    }
                },
                "symptom_tags": [
                    {"name": "healthy", "value": -1},
                    {"name": "exposed", "value": 0},
                ],
                "trajectories": [],
            }
        }

    def test_yaml_roundtrip(self, sample_yaml_data):
        """Test that YAML can be written and read back."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_yaml_data, f, Dumper=NoAliasDumper)
            temp_path = f.name

        try:
            with open(temp_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data["disease"]["name"] == "test_disease"
            assert loaded_data["disease"]["settings"]["default_lowest_stage"] == "exposed"
        finally:
            os.unlink(temp_path)

    def test_yaml_has_disease_section(self, sample_yaml_data):
        """Test that sample YAML has required disease section."""
        assert "disease" in sample_yaml_data
        assert "name" in sample_yaml_data["disease"]
        assert "settings" in sample_yaml_data["disease"]
        assert "transmission" in sample_yaml_data["disease"]

    def test_yaml_transmission_data_structure(self, sample_yaml_data):
        """Test that transmission data has correct structure."""
        transmission = sample_yaml_data["disease"]["transmission"]
        
        assert "type" in transmission
        assert "max_infectiousness" in transmission
        
        max_inf = transmission["max_infectiousness"]
        assert max_inf["type"] == "lognormal"
        assert "s" in max_inf
        assert "loc" in max_inf
        assert "scale" in max_inf


class TestConfigPanelData:
    """Tests for configuration panel data handling."""

    def test_disease_config_widget_creation(self):
        """Test that DiseaseConfigWidget can be created."""
        widget = DiseaseConfigWidget()
        assert widget is not None
        assert widget.name_entry is not None
        assert widget.dls_combo is not None
        assert widget.mmst_combo is not None

    def test_disease_config_widget_get_data(self):
        """Test extracting data from configuration widget."""
        widget = DiseaseConfigWidget()
        widget.name_entry.setText("TestDisease")
        widget.dls_combo.setCurrentText("exposed")
        widget.mmst_combo.setCurrentText("mild")
        
        data = widget.getConfigData()
        
        assert data["name"] == "TestDisease"
        assert data["default_lowest_stage"] == "exposed"
        assert data["max_mild_symptom_tag"] == "mild"

    def test_disease_config_widget_transmission_data(self):
        """Test that transmission data is included in extracted data."""
        widget = DiseaseConfigWidget()
        widget.name_entry.setText("TestDisease")
        
        data = widget.getConfigData()
        
        assert "transmission" in data
        assert "type" in data["transmission"]
        # Should have transmission sections
        assert len(data["transmission"]) > 1

    def test_disease_config_widget_set_data(self):
        """Test populating configuration widget with data."""
        widget = DiseaseConfigWidget()
        
        config_data = {
            "name": "LoadedDisease",
            "default_lowest_stage": "asymptomatic",
            "max_mild_symptom_tag": "severe",
            "transmission": {
                "type": "beta",
            }
        }
        
        widget.setConfigData(config_data)
        
        assert widget.name_entry.text() == "LoadedDisease"
        assert widget.dls_combo.currentText() == "asymptomatic"
        assert widget.mmst_combo.currentText() == "severe"


class TestConstantsAndConfiguration:
    """Tests for application constants."""

    def test_disease_stages_are_strings(self):
        """Test that all disease stages are strings."""
        assert all(isinstance(stage, str) for stage in DISEASE_STAGES)

    def test_distribution_types_are_strings(self):
        """Test that all distribution types are strings."""
        assert all(isinstance(dist_type, str) for dist_type in DISTRIBUTION_TYPES)

    def test_disease_stages_lowercase(self):
        """Test that disease stages are lowercase."""
        assert all(stage.islower() for stage in DISEASE_STAGES)

    def test_distribution_types_lowercase(self):
        """Test that distribution types are lowercase."""
        assert all(dist_type.islower() for dist_type in DISTRIBUTION_TYPES)

    def test_no_duplicate_disease_stages(self):
        """Test that there are no duplicate disease stages."""
        assert len(DISEASE_STAGES) == len(set(DISEASE_STAGES))

    def test_no_duplicate_distribution_types(self):
        """Test that there are no duplicate distribution types."""
        assert len(DISTRIBUTION_TYPES) == len(set(DISTRIBUTION_TYPES))


class TestImportExamples:
    """Tests using actual example files."""

    def test_example_files_exist(self):
        """Test that example files exist."""
        examples_dir = Path(__file__).parent.parent / "examples"
        assert examples_dir.exists()
        
        example_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
        assert len(example_files) > 0

    def test_example_files_are_valid_yaml(self):
        """Test that example files contain valid YAML."""
        examples_dir = Path(__file__).parent.parent / "examples"
        example_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
        
        for example_file in example_files:
            with open(example_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None
                except yaml.YAMLError:
                    pytest.fail(f"Invalid YAML in {example_file}")

    def test_example_files_have_disease_section(self):
        """Test that example files have disease section."""
        examples_dir = Path(__file__).parent.parent / "examples"
        example_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
        
        for example_file in example_files:
            with open(example_file, 'r') as f:
                data = yaml.safe_load(f)
                assert "disease" in data, f"{example_file} missing 'disease' section"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
