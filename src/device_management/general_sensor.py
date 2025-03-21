class Sensor:
    """
    class to hold all properties of a sensor
    """

    def __init__(self, sensor_type: str, paramters: dict) -> None:
        # self.type = type
        # self.srn = srn
        # self.device = device
        # self.channel_num = channel_num
        self.sensor_type = sensor_type
        self.parameters = paramters
        if self.parameters["Channel_ID"] == "":
            raise Warning(f"Sensor ID {self.parameters['ID']} is attached to a channel.")
        if not self.parameters["available"]:
            raise ValueError(
                f"Sensor ID {
                    self.parameters['ID']} is not available."
            )
        return None

    def __str__(self):
        return f"{self.sensor_type} Sensor: {self.parameters}"


temp_params = {
    "Type": "Temperature Sensor",
    "ID": "001",
    "available": True,
    "measurement_range": (0, 100),
    "unit": "Celsius",
    "accuracy": "±0.5°C",
    "calibration_date": "2024-01-01",
    "usage": "loacation, fastening...",
}

pressure_params = {
    "Type": "Preasure Sensor",
    "ID": "001",
    "available": True,
    "measurement_range": (1, 10),
    "unit": "Bar",
    "accuracy": "±0.1 Bar",
    "calibration_date": "2024-01-05",
}

geophone_params = {
    "Channel_ID": "",
    "Type": "Geophone",
    "ID": "001",
    "available": True,
    "name": "HG-6-001",
    "orientation": "horizontal x",
    "location": "floor",
    "fasting": "spicks",
    "measurement_range": (-150, 150),  # mm/s
    "unit": "mm/s",
    "accuracy": 0.005,  # ±mm/s
    "calibration_date": "2024-01-05",
    "natural_frequency": 4.5,  # Hz
    "damping": "0.56",  # *100 = %
    "resistance": 375,  # ohm
    "sensitivity": 28.8,  # V/(mm/s)
    "moving_mass": 11.1,  # g
    "max_coil_excursion": 4,  # mm
    "scaling_factor": 34.72,  # 1000/sensitivity
}

if __name__ == "__main__":
    h6_001 = Sensor("Geophone", geophone_params)
    print(h6_001.parameters["natural_frequency"])
