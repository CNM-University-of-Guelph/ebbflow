import pytest
from ebbflow import ACSL

@pytest.fixture
def valid_model():
    class ValidModel(ACSL):
        @ACSL.INITIAL
        def initial(self):
            pass
            
        @ACSL.DYNAMIC
        def dynamic(self):
            pass
            
        @ACSL.DERIVATIVE
        def derivative(self):
            pass
            
        @ACSL.DISCRETE
        def discrete(self):
            pass
            
        @ACSL.TERMINAL
        def terminal(self):
            pass
    return ValidModel()


@pytest.fixture
def duplicate_sections_model():
    class DuplicateModel(ACSL):
        @ACSL.INITIAL
        def initial1(self):
            pass
            
        @ACSL.INITIAL
        def initial2(self):
            pass
    return DuplicateModel


@pytest.fixture
def orphaned_derivative_model():
    class OrphanedDerivativeModel(ACSL):
        @ACSL.INITIAL
        def initial(self):
            pass
            
        @ACSL.DERIVATIVE
        def derivative(self):
            pass
    return OrphanedDerivativeModel


@pytest.fixture
def orphaned_discrete_model():
    class OrphanedDiscreteModel(ACSL):
        @ACSL.DISCRETE
        def discrete(self):
            pass
    return OrphanedDiscreteModel


class TestSectionValidation:
    def test_valid_model_creation(self, valid_model):
        """Test that a valid model can be created without raising exceptions"""
        assert isinstance(valid_model, ACSL)
        
    def test_duplicate_section_detection(self, duplicate_sections_model):
        """Test that duplicate sections are detected and raise an error"""
        with pytest.raises(ValueError) as exc_info:
            model = duplicate_sections_model()
        assert "Duplicate section: INITIAL" in str(exc_info.value)
        
    def test_orphaned_derivative_detection(self, orphaned_derivative_model):
        """Test that derivative section without dynamic section raises an error"""
        with pytest.raises(ValueError) as exc_info:
            model = orphaned_derivative_model()
        assert "DERIVATIVE section requires DYNAMIC section" in str(exc_info.value)
        
    def test_orphaned_discrete_detection(self, orphaned_discrete_model):
        """Test that discrete section without dynamic section raises an error"""
        with pytest.raises(ValueError) as exc_info:
            model = orphaned_discrete_model()
        assert "DISCRETE section requires DYNAMIC section" in str(exc_info.value)
        
    def test_optional_sections(self):
        """Test that models can be created with only some sections"""
        class MinimalModel(ACSL):
            @ACSL.INITIAL
            def initial(self):
                pass
                
            @ACSL.DYNAMIC
            def dynamic(self):
                pass
                
        model = MinimalModel()
        assert isinstance(model, ACSL)
        
    def test_section_order_independence(self):
        """Test that sections can be defined in any order"""
        class OutOfOrderModel(ACSL):
            @ACSL.TERMINAL
            def terminal(self):
                pass
                
            @ACSL.DYNAMIC
            def dynamic(self):
                pass
                
            @ACSL.INITIAL
            def initial(self):
                pass
                
        model = OutOfOrderModel()
        assert isinstance(model, ACSL)
