import json
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AdminSyncService:
    """
    Service to sync plot data between Django and Admin.py FastAPI service
    """
    
    def __init__(self):
        self.admin_api_url = getattr(settings, 'ADMIN_API_URL', 'http://localhost:7030')
        self.username = getattr(settings, 'ADMIN_API_USERNAME', 'devuser')
        self.password = getattr(settings, 'ADMIN_API_PASSWORD', 'KGZvvyd*9k')
        self.auth = HTTPBasicAuth(self.username, self.password)
    
    def sync_plot_to_admin(self, plot_instance) -> bool:
        """
        Sync a single plot to the Admin.py service
        
        Args:
            plot_instance: Plot model instance
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            # Prepare plot data for Admin.py
            plot_data = self._prepare_plot_data(plot_instance)
            
            # Send to Admin.py API
            response = requests.post(
                f"{self.admin_api_url}/sync/plot",
                json=plot_data,
                headers={'Content-Type': 'application/json'},
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully synced plot {plot_instance.id} to Admin.py")
                return True
            else:
                logger.error(f"Failed to sync plot {plot_instance.id} to Admin.py: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing plot {plot_instance.id} to Admin.py: {str(e)}")
            return False
    
    def _prepare_plot_data(self, plot_instance) -> Dict[str, Any]:
        """
        Prepare plot data in the format expected by Admin.py
        """
        plot_data = {
            "id": plot_instance.id,
            "name": self._generate_plot_name(plot_instance),
            "properties": {
                "Name": self._generate_plot_name(plot_instance),
                "Description": f"GAT: {plot_instance.gat_number}, Plot: {plot_instance.plot_number or 'N/A'}, Village: {plot_instance.village or 'Unknown'}",
                "gat_number": plot_instance.gat_number,
                "plot_number": plot_instance.plot_number,
                "village": plot_instance.village,
                "taluka": plot_instance.taluka,
                "district": plot_instance.district,
                "state": plot_instance.state,
                "country": plot_instance.country,
                "pin_code": plot_instance.pin_code
            },
            "geometry": {
                "type": "Polygon" if plot_instance.boundary else "Point",
                "coordinates": []
            }
        }
        
        # Handle geometry data
        if plot_instance.boundary:
            # Convert PolygonField to coordinates
            coords = list(plot_instance.boundary.coords[0])
            plot_data["geometry"]["coordinates"] = [coords]
        elif plot_instance.location:
            # Convert PointField to coordinates
            coords = [plot_instance.location.x, plot_instance.location.y, 0.0]
            plot_data["geometry"]["coordinates"] = coords
            plot_data["geometry"]["type"] = "Point"
        else:
            # No geometry data - provide a default structure
            plot_data["geometry"] = {
                "type": "Point",
                "coordinates": [0.0, 0.0, 0.0]
            }
        
        return plot_data
    
    def _generate_plot_name(self, plot_instance) -> str:
        """
        Generate a plot name for Admin.py
        """
        if plot_instance.gat_number and plot_instance.plot_number:
            return f"{plot_instance.gat_number}_{plot_instance.plot_number}"
        elif plot_instance.gat_number:
            return plot_instance.gat_number
        else:
            return f"plot_{plot_instance.id}"
    
    def sync_all_plots(self) -> bool:
        """
        Sync all plots to Admin.py service
        
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            from .models import Plot
            
            plots = Plot.objects.all()
            plot_list = []
            
            for plot in plots:
                plot_data = self._prepare_plot_data(plot)
                plot_list.append(plot_data)
            
            # Send to Admin.py API
            response = requests.post(
                f"{self.admin_api_url}/sync/plots",
                json={"plots": plot_list},
                headers={'Content-Type': 'application/json'},
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully synced {len(plot_list)} plots to Admin.py")
                return True
            else:
                logger.error(f"Failed to sync plots to Admin.py: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing plots to Admin.py: {str(e)}")
            return False
    
    def delete_plot_from_admin(self, plot_id: int) -> bool:
        """
        Delete a plot from Admin.py service
        
        Args:
            plot_id: Plot ID to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.admin_api_url}/sync/plot/{plot_id}",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted plot {plot_id} from Admin.py")
                return True
            else:
                logger.error(f"Failed to delete plot {plot_id} from Admin.py: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting plot {plot_id} from Admin.py: {str(e)}")
            return False
    
    def get_sar_analysis(self, plot_name: str, start_date: str = None, end_date: str = None) -> Optional[Dict[str, Any]]:
        """
        Get SAR analysis for a specific plot from Admin.py
        
        Args:
            plot_name: Plot name to analyze
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict with SAR analysis data or None if failed
        """
        try:
            params = {"plot_name": plot_name}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
                
            response = requests.post(
                f"{self.admin_api_url}/analyze",
                params=params,
                auth=self.auth,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get SAR analysis for {plot_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting SAR analysis for {plot_name}: {str(e)}")
            return None
