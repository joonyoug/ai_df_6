# sms_sender.py
import vonage

class SMSSender:
    def __init__(self, key, secret):
        self.client = vonage.Client(key=key, secret=secret)
        self.sms = vonage.Sms(self.client)

    def send_sms(self, to, text):
        responseData = self.sms.send_message(
            {
                "from": "Vonage APIs",
                "to": to,
                "text": text,
            }
        )

        if responseData["messages"][0]["status"] == "0":
            print("메시지 전송 성공.")
        else:
            print(f"메시지 전송 실패: {responseData['messages'][0]['error-text']}")

