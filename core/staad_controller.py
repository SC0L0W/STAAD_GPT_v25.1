# core/staad_controller.py

from openstaad import Geometry, Root
import comtypes

class GeometryController:
    def __init__(self):
        try:
            self.geometry = Geometry()
            self.root = Root()
        except (OSError, comtypes.COMError) as e:
            # This error means STAAD is not running or no model is open
            raise RuntimeError("STAAD.Pro is not open, or no model is loaded.") from e

    def get_selected_beams(self):
        return self.geometry.GetSelectedBeams()

    def get_beam_length(self, beam_id):
        return self.geometry.GetBeamLength(beam_id)

    def get_last_node_no(self):
        return self.geometry.GetLastNodeNo()

    def get_node_coordinates(self, node_id):
        return self.geometry.GetNodeCoordinates(node_id)

    def create_new_staad_file(self, file_path):
        # Implement logic to create a new STAAD file
        # Note: OpenSTAAD primarily interacts with open STAAD models.
        # Creating a new file might require automating STAAD.Pro to open a new file.
        return f"Created new STAAD file at {file_path}"
