from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Farm, Plot, CropType, SoilType, Industry, Irrigation
from .farmer_registration_service import CompleteFarmerRegistrationService
from users.models import Role

User = get_user_model()


class MultiplePlotsRegistrationTest(TestCase):
    """Test that multiple plots can be registered without CropType duplicate errors"""
    
    def setUp(self):
        """Set up test data"""
        # Create industry
        self.industry = Industry.objects.create(
            name="Test Industry",
            description="Test Industry Description"
        )
        
        # Create field officer role
        self.field_officer_role, _ = Role.objects.get_or_create(
            name='fieldofficer',
            defaults={'display_name': 'Field Officer'}
        )
        
        # Create field officer user
        self.field_officer = User.objects.create_user(
            username='fieldofficer1',
            email='fieldofficer@test.com',
            password='testpass123',
            phone_number='9876543210',
            role=self.field_officer_role,
            industry=self.industry
        )
        
        # Create farmer role
        self.farmer_role, _ = Role.objects.get_or_create(
            name='farmer',
            defaults={'display_name': 'Farmer'}
        )
    
    def test_multiple_plots_same_crop_type_name(self):
        """Test registering multiple plots with same crop type name doesn't cause duplicate error"""
        
        registration_data = {
            "farmer": {
                "username": "test_farmer_multi",
                "email": "testmulti@example.com",
                "password": "farm@123",
                "first_name": "Test",
                "last_name": "Farmer",
                "phone_number": "9111111111",
                "address": "Test Village",
                "village": "Test Village",
                "district": "Test District",
                "state": "Maharashtra",
                "taluka": "Test Taluka"
            },
            "plots": [
                {
                    "plot": {
                        "gat_number": "TEST001",
                        "plot_number": "001",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {
                            "type": "Point",
                            "coordinates": [74.215, 19.567]
                        }
                    },
                    "farm": {
                        "address": "Farm 1",
                        "area_size": "2.5",
                        "spacing_a": "3.0",
                        "spacing_b": "1.5",
                        "soil_type_name": "Loamy",
                        "crop_type_name": "Sugarcane",
                        "plantation_type": "adsali",
                        "planting_method": "3_bud"
                    },
                    "irrigation": {
                        "irrigation_type_name": "drip",
                        "status": True,
                        "flow_rate_lph": 2.5,
                        "emitters_count": 150
                    }
                },
                {
                    "plot": {
                        "gat_number": "TEST002",
                        "plot_number": "002",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {
                            "type": "Point",
                            "coordinates": [74.216, 19.568]
                        }
                    },
                    "farm": {
                        "address": "Farm 2",
                        "area_size": "3.0",
                        "spacing_a": "2.0",
                        "spacing_b": "1.0",
                        "soil_type_name": "Black Soil",
                        "crop_type_name": "Sugarcane",  # Same crop type name
                        "plantation_type": "suru",  # Different plantation type
                        "planting_method": "2_bud"  # Different planting method
                    },
                    "irrigation": {
                        "irrigation_type_name": "flood",
                        "motor_horsepower": 7.5,
                        "pipe_width_inches": 4.0,
                        "distance_motor_to_plot_m": 50.0
                    }
                },
                {
                    "plot": {
                        "gat_number": "TEST003",
                        "plot_number": "003",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {
                            "type": "Point",
                            "coordinates": [74.217, 19.569]
                        }
                    },
                    "farm": {
                        "address": "Farm 3",
                        "area_size": "4.0",
                        "spacing_a": "3.5",
                        "spacing_b": "2.0",
                        "soil_type_name": "Red Soil",
                        "crop_type_name": "Sugarcane",  # Same crop type name
                        "plantation_type": "adsali",  # Same as first plot
                        "planting_method": "3_bud"  # Same as first plot
                    },
                    "irrigation": {
                        "irrigation_type_name": "drip",
                        "status": True,
                        "flow_rate_lph": 3.0,
                        "emitters_count": 200
                    }
                }
            ]
        }
        
        # This should NOT raise MultipleObjectsReturned error
        try:
            result = CompleteFarmerRegistrationService.register_complete_farmer(
                registration_data,
                self.field_officer
            )
            
            # Verify registration was successful
            self.assertIsNotNone(result)
            self.assertTrue(result.get('success', False))
            self.assertIn('farmer', result)
            self.assertIn('entities', result)
            
            # Verify farmer was created
            farmer = User.objects.get(username="test_farmer_multi")
            self.assertEqual(farmer.email, "testmulti@example.com")
            self.assertEqual(farmer.role.name, 'farmer')
            
            # Verify all plots were created
            plots = Plot.objects.filter(farmer=farmer)
            self.assertEqual(plots.count(), 3)
            
            # Verify all farms were created
            farms = Farm.objects.filter(farm_owner=farmer)
            self.assertEqual(farms.count(), 3)
            
            # Verify CropTypes were handled correctly
            # First and third plot should use the same CropType (same crop_type, plantation_type, planting_method, industry)
            crop_types = CropType.objects.filter(crop_type="Sugarcane", industry=self.industry)
            
            # We should have at least one CropType
            self.assertGreater(crop_types.count(), 0)
            
            # Check that first and third farms share the same CropType
            farm1 = Farm.objects.filter(farm_owner=farmer, address="Farm 1").first()
            farm3 = Farm.objects.filter(farm_owner=farmer, address="Farm 3").first()
            
            if farm1 and farm3:
                # They should have the same CropType if they match exactly
                if (farm1.crop_type and farm3.crop_type and
                    farm1.crop_type.plantation_type == farm3.crop_type.plantation_type and
                    farm1.crop_type.planting_method == farm3.crop_type.planting_method):
                    self.assertEqual(farm1.crop_type.id, farm3.crop_type.id)
            
            print("\n✅ Test passed: Multiple plots with same crop type registered successfully!")
            print(f"   Created {plots.count()} plots and {farms.count()} farms")
            
        except Exception as e:
            self.fail(f"Registration failed with error: {str(e)}\nError type: {type(e).__name__}")
    
    def test_multiple_plots_exact_same_crop_type(self):
        """Test that multiple plots with exactly the same crop type parameters share the same CropType"""
        
        registration_data = {
            "farmer": {
                "username": "test_farmer_exact",
                "email": "testexact@example.com",
                "password": "farm@123",
                "first_name": "Test",
                "last_name": "Exact",
                "phone_number": "9222222222",
                "address": "Test Village",
                "village": "Test Village",
                "district": "Test District",
                "state": "Maharashtra",
                "taluka": "Test Taluka"
            },
            "plots": [
                {
                    "plot": {
                        "gat_number": "EXACT001",
                        "plot_number": "001",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {"type": "Point", "coordinates": [74.215, 19.567]}
                    },
                    "farm": {
                        "address": "Exact Farm 1",
                        "area_size": "2.5",
                        "soil_type_name": "Loamy",
                        "crop_type_name": "Wheat",
                        "plantation_type": "adsali",
                        "planting_method": "3_bud"
                    },
                    "irrigation": {
                        "irrigation_type_name": "drip",
                        "status": True,
                        "flow_rate_lph": 2.5
                    }
                },
                {
                    "plot": {
                        "gat_number": "EXACT002",
                        "plot_number": "002",
                        "village": "Test Village",
                        "taluka": "Test Taluka",
                        "district": "Test District",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin_code": "422605",
                        "location": {"type": "Point", "coordinates": [74.216, 19.568]}
                    },
                    "farm": {
                        "address": "Exact Farm 2",
                        "area_size": "3.0",
                        "soil_type_name": "Black Soil",
                        "crop_type_name": "Wheat",  # Same as plot 1
                        "plantation_type": "adsali",  # Same as plot 1
                        "planting_method": "3_bud"  # Same as plot 1
                    },
                    "irrigation": {
                        "irrigation_type_name": "flood",
                        "motor_horsepower": 7.5
                    }
                }
            ]
        }
        
        # This should create only ONE CropType for both farms
        result = CompleteFarmerRegistrationService.register_complete_farmer(
            registration_data,
            self.field_officer
        )
        
        # Verify success
        self.assertTrue(result.get('success', False))
        
        farmer = User.objects.get(username="test_farmer_exact")
        farms = Farm.objects.filter(farm_owner=farmer)
        self.assertEqual(farms.count(), 2)
        
        # Both farms should reference the same CropType
        farm1 = farms.filter(address="Exact Farm 1").first()
        farm2 = farms.filter(address="Exact Farm 2").first()
        
        if farm1.crop_type and farm2.crop_type:
            self.assertEqual(farm1.crop_type.id, farm2.crop_type.id)
            print(f"\n✅ Test passed: Both farms share the same CropType (ID: {farm1.crop_type.id})")
        
        # Verify only one CropType exists for this combination
        crop_types = CropType.objects.filter(
            crop_type="Wheat",
            plantation_type="adsali",
            planting_method="3_bud",
            industry=self.industry
        )
        self.assertEqual(crop_types.count(), 1)