#!/usr/bin/env python3
"""
Smart Infusion Device Controller
Manages IV bottle replacement automation using liquid level sensor and servo motor
"""

import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import serial only if needed (not in simulation mode)
try:
    import serial
except ImportError:
    serial = None


class InfusionDeviceController:
    """Controller for the smart infusion device"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, simulate=False):
        """
        Initialize the infusion device controller
        
        Args:
            port: Serial port for Arduino communication
            baudrate: Serial communication speed
            simulate: If True, runs in simulation mode without hardware
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_running = False
        self.simulate = simulate
        self.bottle_count = 1
        self.sensor_value = 500  # Start with high value (bottle full)
        
    def connect(self):
        """Establish connection with Arduino"""
        if self.simulate:
            logger.info("SIMULATION MODE: Connected (no hardware)")
            return True
        
        if not serial:
            logger.error("pyserial not installed. Install with: pip install pyserial")
            return False
        
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            logger.info(f"Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self):
        """Close Arduino connection"""
        if self.simulate:
            logger.info("SIMULATION MODE: Disconnected")
            return
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from Arduino")
    
    def read_sensor(self):
        """Read liquid level sensor value"""
        if self.simulate:
            # Simulate sensor readings: gradually decrease as bottle drains
            self.sensor_value = max(0, self.sensor_value - 15)
            logger.info(f"SIMULATION: Sensor reading = {self.sensor_value}")
            return str(self.sensor_value)
        
        try:
            if self.serial_conn and self.serial_conn.is_open:
                if self.serial_conn.in_waiting:
                    data = self.serial_conn.readline().decode().strip()
                    return data
        except Exception as e:
            logger.error(f"Error reading sensor: {e}")
        return None
    
    def rotate_bottle(self):
        """Send command to rotate next bottle"""
        if self.simulate:
            self.bottle_count += 1
            self.sensor_value = 500  # Reset sensor for new bottle
            logger.warning(f"SIMULATION: Bottle {self.bottle_count} deployed")
            return True
        
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.write(b'ROTATE\n')
                logger.info("Bottle rotation command sent")
                return True
        except Exception as e:
            logger.error(f"Error rotating bottle: {e}")
        return False
    
    def check_bottle_empty(self, sensor_threshold=100):
        """
        Check if current bottle is empty
        
        Args:
            sensor_threshold: Sensor value below which bottle is considered empty
            
        Returns:
            True if bottle is empty, False otherwise
        """
        sensor_value = self.read_sensor()
        if sensor_value:
            try:
                value = int(sensor_value)
                return value < sensor_threshold
            except ValueError:
                logger.warning(f"Invalid sensor value: {sensor_value}")
        return False
    
    def run(self):
        """Main control loop"""
        self.is_running = True
        logger.info("Smart Infusion Device started")
        
        # For simulation, limit runtime to 60 seconds
        sim_start_time = time.time() if self.simulate else None
        
        try:
            while self.is_running:
                # Check simulation timeout
                if self.simulate and (time.time() - sim_start_time) > 60:
                    logger.info("SIMULATION: 60-second test complete")
                    break
                
                # Check if bottle is empty
                if self.check_bottle_empty():
                    logger.warning("Bottle empty - initiating rotation")
                    self.rotate_bottle()
                    time.sleep(5)  # Wait for rotation to complete
                
                time.sleep(1)  # Check every second
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.is_running = False
            self.disconnect()
    
    def stop(self):
        """Stop the control loop"""
        self.is_running = False


def main():
    """Main entry point"""
    import sys
    
    # Check for command line arguments
    simulate = '--simulate' in sys.argv or len(sys.argv) == 1  # Default to simulation
    
    logger.info("Initializing Smart Infusion Device")
    if simulate:
        logger.info(">>> RUNNING IN SIMULATION MODE <<<")
    
    # Create controller instance
    controller = InfusionDeviceController(simulate=simulate)
    
    # Connect to Arduino
    if not controller.connect():
        logger.error("Failed to initialize device")
        return
    
    # Run main control loop
    try:
        controller.run()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        controller.disconnect()
        logger.info("Smart Infusion Device shutdown complete")


if __name__ == "__main__":
    main()
