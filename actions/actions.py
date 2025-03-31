from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd
import random
class ActionRecommendGift(Action):
    def name(self) -> Text:
        return "action_recommend_gift"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # قراءة البيانات من الملف النصي
        try:
            data = []
            with open("/workspaces/codespaces-quickstart/docs/sampleDocument.txt", "r", encoding="utf-8") as file:
                entry = {}
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('---'):  # تجاهل الأسطر الفاصلة
                        if entry:
                            data.append(entry)
                            entry = {}
                        continue
                    key, value = line.split(":", 1)
                    entry[key.strip().lower().replace(" ", "_")] = value.strip()

            if entry:  # إضافة آخر عنصر
                data.append(entry)

            df = pd.DataFrame(data)

            # التأكد أن الأعمدة موجودة
            expected_columns = {"gift_name", "description", "price_range", "occasion", "recipient_type"}
            if not expected_columns.issubset(df.columns):
                dispatcher.utter_message(text="Error: Missing required columns in the dataset.")
                return []
            
        except Exception as e:
            dispatcher.utter_message(text="Error: Unable to read the gift file.")
            return []

        # استخراج المدخلات من الـ Slots
        recipient_type = tracker.get_slot("recipient_type")
        occasion = tracker.get_slot("occasion")

        # تصفية الهدايا بناءً على المدخلات
        filtered_df = df.copy()
        if recipient_type:
            filtered_df = filtered_df[
                (filtered_df['recipient_type'].str.lower() == recipient_type.lower()) | 
                (filtered_df['recipient_type'] == 'all')
            ]
        if occasion:
            filtered_df = filtered_df[
                (filtered_df['occasion'].str.lower() == occasion.lower()) | 
                (filtered_df['occasion'] == 'general')
            ]

        # إذا لم يتم العثور على هدايا، استخدام الخيارات العامة
        if filtered_df.empty:
            filtered_df = df[df['occasion'] == 'general']

        # اختيار 3 هدايا عشوائيًا
        num_recommendations = min(3, len(filtered_df))
        recommendations = filtered_df.sample(n=num_recommendations) if num_recommendations > 0 else pd.DataFrame()

        # ✅ تأكد أن هناك هدايا فعلًا
        if recommendations.empty:
            dispatcher.utter_message(text="❌ Sorry, no suitable gifts found.")
            return []

        # إرسال العنوان أولًا
        dispatcher.utter_message(text="🎁 **Here are some gift recommendations:**")

        # إرسال كل هدية في رسالة منفصلة
        for _, gift in recommendations.iterrows():
            message = f"🎀 *{gift['gift_name']}*\n"
            message += f"📖 {gift['description']}\n"
            message += f"💰 Price: {gift['price_range']}\n"
            dispatcher.utter_message(text=message)

        return []
