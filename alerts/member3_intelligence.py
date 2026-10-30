import time
import logging

# Configure logging to see what the system is doing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MatchVerification:
    """
    Module 8: Match Verification
    Verifies whether the confidence satisfies the predefined threshold.
    """
    def __init__(self, confidence_threshold=90.0):
        self.confidence_threshold = confidence_threshold

    def verify_match(self, person_details, confidence_score, captured_scene):
        """
        Checks if the recognition confidence meets the required threshold.
        Returns:
            tuple: (is_match (bool), match_data (dict))
        """
        if confidence_score >= self.confidence_threshold:
            logging.info(f"Match Verified for {person_details.get('Name', 'Unknown')}. Score: {confidence_score}%")
            return True, {
                "person_details": person_details,
                "confidence_score": confidence_score,
                "captured_scene": captured_scene,
                "time": time.strftime("%I:%M %p")
            }
        else:
            logging.info(f"Match Failed. Score: {confidence_score}% is below threshold {self.confidence_threshold}%")
            return False, None


class SmartAlertSystem:
    """
    Module 9: Smart Alert System
    Immediately informs the operator using popups, audio, and mobile notifications.
    """
    def __init__(self):
        pass

    def trigger_popup(self, match_data):
        """Displays a desktop popup notification and console output."""
        # (Optional) Future enhancement: Desktop notifications via plyer
        # We rely on the clean Dashboard Console Output for the review.
            
        # Console Display output (Dashboard Mockup)
        print("\n" + "="*40)
        print("*** MATCH FOUND ***")
        print(f"Name:       {match_data['person_details'].get('Name')}")
        print(f"Confidence: {match_data['confidence_score']}%")
        print(f"Time:       {match_data['time']}")
        print(f"Camera:     {match_data.get('camera_source', 'Live Camera')}")
        print("="*40 + "\n")

    def play_audio_alarm(self):
        """Plays an audio alarm to alert the operator."""
        # Uses built-in Windows sound beep. For other OS, can use playsound library.
        try:
            import winsound
            # Play a system beep as an alarm (frequency 2500Hz, duration 1000ms)
            winsound.Beep(2500, 1000) 
        except ImportError:
            logging.warning("winsound not available. Audio alarm skipped.")

    def send_mobile_notification(self, match_data):
        """Sends a mobile notification (Mock implementation)."""
        # In a real project, this would use an API like Twilio (SMS), Firebase, or Pushbullet.
        logging.info("Sending Mobile Notification...")
        logging.info(f"--> SMS/Push sent: Match found for {match_data['person_details'].get('Name')} with {match_data['confidence_score']}% confidence.")

    def generate_alert(self, match_data):
        """
        Triggers all alert mechanisms.
        """
        logging.info("Generating Smart Alerts...")
        self.play_audio_alarm()
        self.trigger_popup(match_data)
        self.send_mobile_notification(match_data)


# ==========================================
# Test Script / Review Demonstration
# ==========================================
if __name__ == "__main__":
    print("--- Initializing Intelligence & Alert Modules (Member 3) ---")
    
    # Initialize Modules
    verifier = MatchVerification(confidence_threshold=95.0)
    alerter = SmartAlertSystem()

    # --- Simulated Data from Member 2 (AI Vision & Recognition) ---
    print("\n--- Simulating Live Feed Input from AI Module ---")
    
    # Scenario 1: High confidence match (Should trigger alert)
    simulated_ai_output_1 = {
        "person_details": {"Name": "Rahul Kumar", "Missing_ID": "MP-1042"},
        "confidence_score": 97.6,
        "captured_scene": "frame_1042_capture.jpg",
        "camera_source": "Mobile Camera"
    }
    
    # Scenario 2: Low confidence match (Should continue monitoring)
    simulated_ai_output_2 = {
        "person_details": {"Name": "Unknown Face", "Missing_ID": "N/A"},
        "confidence_score": 82.1,
        "captured_scene": "frame_1043_capture.jpg",
        "camera_source": "CCTV_North_Gate"
    }

    # --- Execute Verification and Alert Workflow ---
    
    print("\n[Processing Frame 1]")
    time.sleep(1) # Simulate real-time delay
    is_match, match_data = verifier.verify_match(
        simulated_ai_output_1["person_details"],
        simulated_ai_output_1["confidence_score"],
        simulated_ai_output_1["captured_scene"]
    )
    if is_match:
        # Add camera source to the match data to display in the alert
        match_data['camera_source'] = simulated_ai_output_1["camera_source"]
        alerter.generate_alert(match_data)

    print("\n[Processing Frame 2]")
    time.sleep(1)
    is_match, match_data = verifier.verify_match(
        simulated_ai_output_2["person_details"],
        simulated_ai_output_2["confidence_score"],
        simulated_ai_output_2["captured_scene"]
    )
    if is_match:
        match_data['camera_source'] = simulated_ai_output_2["camera_source"]
        alerter.generate_alert(match_data)
    else:
        print("Match confidence below threshold. System continues monitoring...")
