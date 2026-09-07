#!/usr/bin/env python
"""
Synthetic Group Chat Dataset Generator.
Generates a realistic Hinglish/code-mixed group chat corpus.
"""

import json
import random
import os
from datetime import datetime, timedelta

random.seed(42)

PARTICIPANTS = ["Priya", "Rohan", "Anjali", "Karan", "Meera", "Vikram", "Sneha", "Amit"]

PARTICIPANT_STYLES = {
    "Priya": {"emoji_freq": 0.3, "typo_freq": 0.05, "short_reply_freq": 0.2},
    "Rohan": {"emoji_freq": 0.4, "typo_freq": 0.08, "short_reply_freq": 0.5},
    "Anjali": {"emoji_freq": 0.1, "typo_freq": 0.02, "short_reply_freq": 0.1},
    "Karan": {"emoji_freq": 0.6, "typo_freq": 0.03, "short_reply_freq": 0.3},
    "Meera": {"emoji_freq": 0.2, "typo_freq": 0.15, "short_reply_freq": 0.4},
    "Vikram": {"emoji_freq": 0.1, "typo_freq": 0.05, "short_reply_freq": 0.1},
    "Sneha": {"emoji_freq": 0.3, "typo_freq": 0.2, "short_reply_freq": 0.3},
    "Amit": {"emoji_freq": 0.2, "typo_freq": 0.05, "short_reply_freq": 0.25},
}

EMOJIS = ["😂", "😊", "👍", "🤔", "🎉", "😅", "😎", "🤗", "😄", "🙏", "💯", "✌️", "👋", "😏", "🤷", "🙈"]

def inject_typo(text):
    if len(text) < 5:
        return text
    r = random.random()
    words = text.split()
    if not words:
        return text
    idx = random.randint(0, len(words) - 1)
    word = words[idx]
    if r < 0.3 and len(word) >= 3:
        i = random.randint(0, len(word) - 2)
        chars = list(word)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        words[idx] = "".join(chars)
    elif r < 0.6 and len(word) >= 4:
        i = random.randint(0, len(word) - 1)
        words[idx] = word[:i] + word[i + 1:]
    elif r < 0.8 and len(word) >= 3:
        i = random.randint(0, len(word) - 1)
        words[idx] = word[:i] + word[i] * 2 + word[i + 1:]
    return " ".join(words)

def maybe_typo(text, sender):
    style = PARTICIPANT_STYLES.get(sender, {})
    if random.random() < style.get("typo_freq", 0.05):
        return inject_typo(text)
    return text

def maybe_emoji(text, sender):
    style = PARTICIPANT_STYLES.get(sender, {})
    if random.random() < style.get("emoji_freq", 0.2):
        return text + " " + random.choice(EMOJIS)
    return text

def maybe_short(text, sender):
    style = PARTICIPANT_STYLES.get(sender, {})
    if random.random() < style.get("short_reply_freq", 0.3):
        replies = ["yes", "no", "ok", "done", "haan", "nahi", "lol", "same",
                   "true", "wait", "fine", "sure", "yeah", "cool", "yep",
                   "nah", "brb", "okie", "thik", "hmm", "kya", "jiyo"]
        return random.choice(replies)
    return text

def random_dt(start, end):
    delta = end - start
    return start + timedelta(seconds=random.uniform(0, delta.total_seconds()))

GENERAL_TEMPLATES = [
    "kya haal hai sabka?",
    "morning everyone",
    "subah bakhar yaad aayi",
    "koi assignment submit kiya?",
    "exam ki taiyari kaise chal rahi hai?",
    "ye paper tough lag raha tha",
    "kal ki class bhi hogyi miss",
    "maaf karo bhai, thoda late ho gaya",
    "weekend plans?",
    "koi movie recommend karega?",
    "today's lecture was so boring 😴",
    "coffee kha liya? need caffeine badly",
    "traffic kharab hai bahut, late lag sakta hai",
    "raat ko free hai kya? study group bana lete hain",
    "project deadline extend ho gaya hai kya?",
    "semester end ke baad kon si movie dekhni hai?",
    "hostel mess mein aaj kya banaya hai?",
    "yaar meri laptop hang ho rahi thi 😭",
    "placement season ka tension bahut hai",
    "interview prep ke liye koi resource?",
    "coding competition ke baare mein koi idea?",
    "next week ka schedule share karo please",
    "library reopens tomorrow morning",
    "campus mein free food event hai aaj",
    "bhai ye assignment ka solution kaise milega?",
    "quiz result declare ho gaya hai",
    "internal assessment ki taiyari karo",
    "last bench pe baithe the na? 🤡",
    "professor ne extra marks diye",
    "syllabus reduce ho gaya hai",
    "attendance mandatory hai ya optional?",
    "lab manual download karke rakho",
    "group photo click karwao sab",
    "next sem mein course selection kab tak?",
    "course evaluation form bharna padega",
    "library books return kar dena",
    "dost, tere notes share kar sakta hu?",
    "assignment deadline kab hai?",
    "ye topic samajh nahi aaya, koi smjhayega?",
    "online class ka recording mil jayega kya?",
    "attendance mein absence kitna allowed hai?",
]

FORWARDED_TEMPLATES = [
    "Forwarded:\nWeekend sale starts tomorrow! 50% off on everything.",
    "Forwarded message:\nImportant notice: Library hours changed.\nNew timings: 8 AM - 10 PM.",
    "Forwarded:\nExam preparation tips:\n1. Start early\n2. Make short notes\n3. Practice past papers",
    "Fwd:\nCampus fest 2024 announcements coming soon!",
    "Forwarded:\nReminder: ID card mandatory for exam entry.",
    "Forwarded message:\nScholarship applications open!\nLast date: 15th of this month.",
    "Forwarded:\nNew menu at canteen from next week!",
]


def make_general_msg(date_range, thread_id="general"):
    sender = random.choice(PARTICIPANTS)
    base_text = random.choice(GENERAL_TEMPLATES)
    text = maybe_short(base_text, sender)
    text = maybe_typo(text, sender)
    text = maybe_emoji(text, sender)
    if random.random() < 0.08:
        text = random.choice(FORWARDED_TEMPLATES)
    ts = random_dt(date_range[0], date_range[1])
    return {
        "sender": sender,
        "timestamp": ts,
        "text": text,
        "month": ts.strftime("%Y-%m"),
        "thread_id": thread_id,
    }



# ── Thread 1: Manali Trip ─────────────────────────────────────────────

def gen_manali_thread(start_date):
    """Generate ~100 messages for the Manali trip decision thread."""
    tid = "thread_manali_trip"
    msgs = []
    t = start_date

    def m(sender, text, d=0, h=0, mi=0, s=0):
        ts = t + timedelta(days=d, hours=h, minutes=mi, seconds=s)
        text = maybe_typo(text, sender)
        text = maybe_emoji(text, sender)
        msgs.append({"sender": sender, "timestamp": ts,
                      "text": text, "month": ts.strftime("%Y-%m"), "thread_id": tid})

    p = PARTICIPANTS

    # Phase 1: Initial suggestion
    m("Priya", "Hey everyone! Summer break ka plan banate hain kya?", 0, 18)
    m("Rohan", "haan bhai, bahut time lag raha tha", 0, 18, 2)
    m("Anjali", "I am free after my exams end on May 10th", 0, 18, 5)
    m("Karan", "Where to? Goa already crowded hai", 0, 18, 10)
    m("Meera", "budget kitna soch rahe ho?", 0, 18, 15)

    # Phase 2: Destination discussion
    m("Vikram", "Depends on budget. Manali should be under 12-15k per person", 1, 10)
    m("Sneha", "Manali achha lagta hai. Weather theek hota hai wahan", 1, 12, 5)
    m("Amit", "Goa is too expensive this time. Water sports etc.", 1, 14)
    m("Priya", "Manali or Mussoorie? Mussoorie is closer", 2, 9)
    m("Rohan", "Manali is fine, just want to go somewhere cool", 2, 9, 3)
    m("Anjali", "Goa would be fun but cost is a concern", 2, 15)
    m("Karan", "Manali me toh paragliding bhi hoti hai, that adds to the fun", 3, 11)
    m("Meera", "paragliding ke liye extra paise lagenge", 3, 11, 2)

    # Phase 3: Budget discussion with disagreement
    m("Vikram", "Let's settle the budget first. 15k max per head. Who can manage?", 4, 8)
    m("Sneha", "15k bohot kam hai for 5-6 days", 4, 19, 10)
    m("Amit", "We can manage if we book shared taxis and budget hotels", 5, 16)
    m("Priya", "Actually 15k is doable if we plan well", 6, 10)
    m("Rohan", "15k? bhai yeh toh sirf transport + hotel ka ho gaya", 6, 14, 5)
    m("Anjali", "I can stretch to 18k but not beyond that", 6, 20)
    m("Karan", "Can we get sponsorship? 😂 kidding", 7, 11)
    m("Vikram", "Ok, 18k it is. But we need firm commitments", 7, 12)
    m("Meera", "count me in for 18k", 7, 15)
    m("Sneha", "me too. But let's track expenses properly", 8, 9, 3)

    # Phase 4: Date discussion
    m("Rohan", "May 15-20? Exam ke baad milke chale jayenge", 9, 14)
    m("Priya", "May 15 se shuru karo, that's right after my exams", 10, 10, 5)
    m("Anjali", "May 15-20 works for me too", 10, 12)
    m("Vikram", "5 din ka plan? Or 4 din?", 11, 8)
    m("Sneha", "4 din is enough. Travel time bhi lagta hai", 11, 18, 2)
    m("Amit", "4 din ka plan bana do. May 15-18", 12, 14)
    m("Karan", "May 15-18? What about May 16-19? More weekend time", 12, 20, 3)
    m("Meera", "15-18 is better, need to be back by 19th for project submission", 13, 9)

    # Phase 5: Transportation
    m("Priya", "Cab or train? Cab is faster but expensive", 14, 10)
    m("Rohan", "Train sasti lagti hai. Overnight journey", 14, 11, 2)
    m("Anjali", "I would prefer a shared cab. Faster and we reach together", 15, 14)
    m("Vikram", "Cab for 8 people should be around 4-5k total, so ~600-700 per person", 16, 9)
    m("Sneha", "Cab booking ka link bhej do koi?", 16, 18, 5)
    m("Amit", "Cab Hi chale is best. Will book after confirming numbers", 17, 12)
    m("Karan", "8-9 baje se jayenge? early morning train jaisa feel", 17, 20, 3)
    m("Meera", "kal subah 6-7 baje pick up karenge", 18, 8)

    # Phase 6: Hotel discussion
    m("Priya", "hotel booking ka kya scene hai?", 19, 10)
    m("Vikram", "Airbnb or hotel? Groups mein Airbnb usually sasti hoti hai", 19, 14, 2)
    m("Rohan", "Airbnb is better, kitchen hota hai, can cook ourselves", 20, 11, 3)
    m("Anjali", "Found a good Airbnb near Mall Road, 3500/night, 2 rooms", 21, 15)
    m("Sneha", "3500 per night? For 3-4 nights that's 10-14k", 21, 18, 1)
    m("Meera", "split karo toh 1200-1500 per person, not bad", 22, 9, 4)
    m("Amit", "Booking confirmed?", 22, 14)

    # Phase 7: Final decision
    m("Priya", "So to confirm: Manali, May 15-18, shared cab, Airbnb booked", 23, 12, 5)
    m("Rohan", "sounds good", 23, 12, 10)
    m("Vikram", "19baje confirm kar do final", 23, 12, 15)

    # Casual filler
    m("Karan", "bhai ye itni si planning se accha toh bas decide karke nikal pade 😂", 23, 14, 2)
    m("Meera", "haan, kabhi kabhi sirf mood ban jata hai", 23, 16, 5)
    m("Sneha", "true that", 23, 16, 10)
    m("Anjali", "But proper planning helps avoid issues later", 23, 18, 3)

    # More discussion
    m("Priya", "packing list banayenge kya?", 24, 9, 3)
    m("Rohan", "just basics, Manali thandi lag sakti hai", 24, 9, 8)
    m("Amit", "temperature range check karo. 10-25 degrees expected", 24, 10, 5)
    m("Karan", "will carry sweater for sure", 24, 11, 2)
    m("Vikram", "anyone bringing camera?", 24, 14, 7)
    m("Meera", "I'll bring mine, for the scenic shots", 24, 14, 12)
    m("Sneha", "phone camera sufficient hai mujhe", 24, 15, 3)
    m("Anjali", "OTP bhej diya maine Airbnb wale, check karo", 24, 16, 10)

    # THE decision message (search target)
    m("Priya", "chalo Manali fix hai 😂", 24, 17, 30)
    msgs[-1]["text"] = "chalo Manali fix hai 😂"  # exempt from typo/emoji injection

    # Follow-up after decision
    m("Rohan", "finally! Manali confirmed", 25, 8, 2)
    m("Karan", "ye toh pura week ka block ho gaya", 25, 9, 5)
    m("Meera", "exact dates: May 15-18, 4 din ka complete plan", 25, 10, 3)
    m("Vikram", "payment schedule banaenge kal", 25, 14, 8)
    m("Sneha", "advance booking amount kitna hai?", 25, 16, 2)
    m("Amit", "total split: cab ~700, Airbnb ~1300, total ~2000 per person", 25, 18, 5)
    m("Anjali", "that includes everything? food exclude karo na?", 26, 9, 3)
    m("Priya", "yes, food and other expenses apart. will track separately", 26, 10, 7)

    # Casual filler to reach ~100
    fillers = [
        ("Manali ki jagah achchi lag rahi hai pics se", "Karan"),
        ("hotel ka address paste karo", "Meera"),
        ("koi emergency contact rakhega?", "Sneha"),
        ("backup plan bhi soch lete hain", "Amit"),
        ("weather forecast dekho kal shaam ko", "Anjali"),
        ("travel insurance ke bare mein bhi baat karenge", "Vikram"),
        ("mobile network kaunse jagah strong rahega", "Priya"),
        ("road trip playlist bana do koi", "Rohan"),
        ("Manali local transport ka plan bhi banaenge", "Meera"),
        ("okie, excited!", "Karan"),
        ("packing list final karo kal raat ko", "Sneha"),
        ("koi pharmacy jaana padega? medicine lena pad sakta hai", "Priya"),
    ]
    for i, (txt, sender) in enumerate(fillers):
        m(sender, txt, 27 + i, random.randint(8, 22), random.randint(0, 59))

    while len(msgs) < 100:
        sender = random.choice(p)
        m(sender, random.choice(GENERAL_TEMPLATES), random.randint(27, 35),
          random.randint(8, 22), random.randint(0, 59))

    msgs.sort(key=lambda x: x["timestamp"])
    dec_idx = next((i for i, x in enumerate(msgs)
                     if "chalo manali fix hai" in x["text"].lower()), None)
    return msgs, dec_idx



# ── Thread 2: House Party ─────────────────────────────────────────────

def gen_house_party_thread(start_date):
    """Generate ~85 messages for the house party decision thread."""
    tid = "thread_house_party"
    msgs = []
    t = start_date

    def m(sender, text, d=0, h=0, mi=0, s=0):
        ts = t + timedelta(days=d, hours=h, minutes=mi, seconds=s)
        text = maybe_typo(text, sender)
        text = maybe_emoji(text, sender)
        msgs.append({"sender": sender, "timestamp": ts,
                      "text": text, "month": ts.strftime("%Y-%m"), "thread_id": tid})

    p = PARTICIPANTS

    # Phase 1: Initial suggestion
    m("Karan", "hey everyone, hostel ke saath mein ek party de sakte hain kya?", 0, 19)
    m("Meera", "party? zaroori hai kya? assignment bhi toh chal raha hai", 0, 19, 3)
    m("Priya", "actually it would be fun! We haven't partied in a while", 1, 10, 2)
    m("Rohan", "count me in! 😎", 1, 11)
    m("Anjali", "I can help with decorations if needed", 1, 14, 5)

    # Phase 2: Venue discussion
    m("Vikram", "venue kahan? hostel common room ya koi flat?", 2, 9)
    m("Sneha", "my flat is available. 2BHK, good for ~15-20 people", 2, 10, 3)
    m("Amit", "flat sound system bhi hoga? music ke liye", 2, 15, 7)
    m("Karan", "Sneha's flat is perfect! location bhi acchi hai", 3, 11, 2)
    m("Meera", "but neighbors complain about noise usually", 3, 14, 4)
    m("Priya", "we can keep volume reasonable, after 9pm tak", 4, 10, 6)
    m("Rohan", "or we can book the college auditorium?", 4, 12, 1)
    m("Anjali", "auditorium se formal lag jayega. flat is better and casual", 5, 16, 3)

    # Phase 3: Date discussion
    m("Vikram", "date finalize karo. next weekend ya usse pehle?", 6, 8)
    m("Sneha", "next weekend works. Saturday March 16th?", 6, 14, 5)
    m("Amit", "March 16? But some of us have quizzes on Monday", 7, 10, 3)
    m("Karan", "march 16 toh sunday hai. perfect timing", 7, 11, 2)
    m("Meera", "what about March 23rd then? After all exams?", 8, 15, 8)
    m("Priya", "March 23 works for me. But March 16 is sooner, more exciting", 9, 10, 4)
    m("Rohan", "March 16! early celebration. I'm free both days anyway", 9, 14, 6)

    # Phase 4: Food discussion
    m("Anjali", "food ka plan? order karenge ya koi chef?", 10, 11, 2)
    m("Vikram", "Zomato order kar sakte hain. 10-12 people ke liye", 11, 10, 5)
    m("Sneha", "pizza + noodles + snacks. everyone likes these", 11, 14, 8)
    m("Amit", "biryani bhi order karo, it's filling and cheap for quantity", 12, 12, 3)
    m("Karan", "burger party! but expensive", 12, 15, 7)
    m("Meera", "budget kitna lag raha hai? per person", 13, 9, 4)
    m("Priya", "roughly 250-300 per person including drinks", 13, 10, 8)
    m("Rohan", "300? thoda mehenga lag raha hai bhai", 14, 11, 2)

    # Phase 5: Guest list
    m("Anjali", "guest list kitni hai expected?", 15, 14, 3)
    m("Vikram", "probably 12-15 people. including plus ones?", 16, 10, 6)
    m("Sneha", "plus ones allowed toh crowd badhega", 16, 15, 9)
    m("Amit", "keep it simple - just group members +1 each max", 17, 12, 4)
    m("Karan", "I'm bringing a friend. hope that's ok", 17, 14, 8)
    m("Meera", "everyone should RSVP so we know exact numbers", 18, 9, 5)
    m("Priya", "please reply with names by March 12", 18, 10, 10)

    # Phase 6: Budget disagreement
    m("Rohan", "total cost kitna padega?", 19, 12, 3)
    m("Vikram", "estimate 2000 total. 12 people = 167 per person", 20, 9, 7)
    m("Anjali", "2000 is a lot for a house party", 20, 14, 2)
    m("Sneha", "but it's for good food and fun. Worth it", 21, 11, 5)
    m("Amit", "could reduce costs by making some snacks at home", 21, 14, 8)
    m("Karan", "no way I'm coming if I have to eat homemade snacks 😂", 22, 10, 3)
    m("Meera", "fine, 2000 it is. But we need to stick to the budget", 22, 12, 8)

    # Phase 7: Final decision
    m("Priya", "Final plan: March 16 (Sat), Sneha's flat, food ordered, budget 2000 total", 23, 10, 6)
    m("Rohan", "sounds good to me!", 23, 10, 10)
    m("Vikram", "confirmed. I'll handle the Zomato order", 23, 11, 2)

    # Casual discussion
    m("Anjali", "playlist koi banayega?", 23, 14, 5)
    m("Sneha", "I have a party playlist on Spotify, share kar dungi", 24, 9, 3)
    m("Amit", "decorations - fairy lights lagayenge", 24, 11, 7)
    m("Karan", "balloons bhi lagegi? basic decorations", 24, 12, 4)
    m("Meera", "simple hi rakh lo, balloons are so last year", 24, 14, 8)
    m("Priya", "lights + some flowers, that's enough", 24, 15, 3)

    # THE decision message (search target)
    m("Priya", "party confirm hai - March 16, Sneha's flat", 25, 10, 30)
    msgs[-1]["text"] = "party confirm hai - March 16, Sneha's flat"

    # Follow-ups
    m("Rohan", "finally! party confirmed", 25, 11, 2)
    m("Sneha", "mujhe bhool jaati thi confirm kar dena 😂", 25, 12, 5)
    m("Vikram", "March 16 is final, mark your calendars", 25, 14, 7)
    m("Anjali", "count me in definitely!", 25, 15, 3)
    m("Amit", "any dress code?", 26, 10, 5)
    m("Karan", "casual dress code. no formals", 26, 11, 2)
    m("Meera", "March 16 = Saturday. Full evening event", 26, 14, 8)
    m("Priya", "6pm se start karenge, till late", 26, 15, 4)

    # Casual filler
    party_fillers = [
        ("need to buy snacks", "Karan"),
        ("bring your own drinks?", "Rohan"),
        ("someone bring speakers", "Vikram"),
        ("sneakers ok for the venue?", "Meera"),
        ("parking space available?", "Sneha"),
        ("can we have bonfire outside?", "Amit"),
        ("need to clean the place before", "Anjali"),
        ("will bring games too", "Priya"),
        ("carpool karenge kya?", "Vikram"),
        ("ice cream bhi order karo", "Meera"),
    ]
    for i, (txt, sender) in enumerate(party_fillers):
        m(sender, txt, 27 + i, random.randint(8, 22), random.randint(0, 59))

    while len(msgs) < 85:
        sender = random.choice(p)
        m(sender, random.choice(GENERAL_TEMPLATES), random.randint(27, 30),
          random.randint(8, 22), random.randint(0, 59))

    msgs.sort(key=lambda x: x["timestamp"])
    dec_idx = next((i for i, x in enumerate(msgs)
                     if "party confirm" in x["text"].lower()), None)
    return msgs, dec_idx



# ── Thread 3: Subscription Sharing ──────────────────────────────────────

def gen_subscription_thread(start_date):
    """Generate ~75 messages for the subscription sharing decision thread."""
    tid = "thread_subscription"
    msgs = []
    t = start_date

    def m(sender, text, d=0, h=0, mi=0, s=0):
        ts = t + timedelta(days=d, hours=h, minutes=mi, seconds=s)
        text = maybe_typo(text, sender)
        text = maybe_emoji(text, sender)
        msgs.append({"sender": sender, "timestamp": ts,
                      "text": text, "month": ts.strftime("%Y-%m"), "thread_id": tid})

    p = PARTICIPANTS

    # Phase 1: Initial suggestion
    m("Amit", "hey, Netflix premium annual 6500 hai. Can we share?", 0, 11, 2)
    m("Meera", "6500 for a year? that's like 540/month", 0, 12, 5)
    m("Rohan", "split kar sakte hain 8 ke beech. ~675 per person", 1, 9, 3)
    m("Anjali", "but simultaneous streams only 4 on premium, na?", 1, 10, 8)
    m("Karan", "4 streams is enough. we can rotate", 1, 14, 2)
    m("Priya", "what about Prime and Spotify too?", 2, 11, 5)

    # Phase 2: Plan discussion
    m("Vikram", "Prime annual 1499. Spotify family 179/month", 2, 15, 7)
    m("Sneha", "Spotify family plan 6 accounts - perfect for 8 of us", 3, 9, 3)
    m("Amit", "total annual cost: Netflix 6500 + Prime 1499 + Spotify 2148 = ~10147", 3, 14, 8)
    m("Meera", "per person = ~1268/year = ~106/month", 4, 10, 4)
    m("Rohan", "106/month? thoda tight hai budget", 4, 11, 2)
    m("Anjali", "can reduce to Spotify + Prime only?", 5, 16, 6)
    m("Karan", "Netflix bhi chahiye na! group movies ke liye", 5, 18, 3)

    # Phase 3: Cost disagreement
    m("Vikram", "actually let's take Netflix premium, Prime, AND Spotify premium", 6, 10, 5)
    m("Sneha", "that's too much. I rarely use Netflix and Spotify both", 6, 14, 8)
    m("Priya", "I use Spotify daily but Netflix once a week", 7, 11, 3)
    m("Meera", "cost cutting karo. Netflix standard bhi chalega, 1200/month", 8, 9, 7)
    m("Rohan", "Netflix standard only 2 screens. 8 people mein divide hone se bekaar", 8, 14, 2)
    m("Amit", "Premium is worth it. more screens, better quality", 9, 10, 4)
    m("Anjali", "ok fine premium. But total monthly should not exceed 150/person", 10, 15, 9)

    # Phase 4: Payment discussion
    m("Karan", "who will be the owner of these accounts?", 11, 12, 3)
    m("Vikram", "I can take Netflix and Prime, since I already have them", 12, 9, 6)
    m("Sneha", "I'll handle Spotify. I get student discount", 12, 10, 8)
    m("Priya", "payment ka hisab bhi lag jayega monthly?", 13, 14, 5)
    m("Meera", "I'll maintain a shared expense sheet on Google Sheets", 13, 15, 10)
    m("Rohan", "monthly split: Netflix 812, Prime 187, Spotify 225 = ~1224 total", 14, 10, 3)
    m("Amit", "per person ~153/month. Close to the 150 limit", 14, 11, 8)
    m("Anjali", "fine, I'll pay my 153 every month", 15, 9, 4)

    # Phase 5: Final decision
    m("Priya", "All agreed: Netflix premium + Prime + Spotify premium", 16, 11, 5)
    m("Rohan", "yes", 16, 11, 8)
    m("Vikram", "starting May 1st", 16, 12, 3)

    # Casual follow-ups
    m("Karan", "otp bhej diya maine spotif y wale, join karo", 16, 14, 7)
    m("Meera", "Netflix ka bhi credentials share karo", 17, 9, 5)
    m("Sneha", "shared the links in our notes app", 17, 10, 3)
    m("Amit", "testing Netflix stream now, works fine", 17, 15, 8)
    m("Anjali", "Spotify join hogaya. thanks!", 18, 11, 4)

    # THE decision message (search target)
    m("Priya", "subscription plan final: Netflix Premium + Prime + Spotify Family @ 153/month each", 19, 10, 30)
    msgs[-1]["text"] = "subscription plan final: Netflix Premium + Prime + Spotify Family @ 153/month each"

    # Follow-ups
    m("Rohan", "finally decided!", 19, 11, 2)
    m("Vikram", "payment schedule: 1st of every month, UPI", 19, 12, 5)
    m("Sneha", "I'll collect from everyone and pay quarterly", 20, 9, 8)
    m("Meera", "Google Sheet link: https://sheets.google.com/...", 20, 10, 3)
    m("Amit", "Netflix premium 4 screens, Prime 2, Spotify 1 family account", 20, 14, 6)
    m("Anjali", "153/month for 3 services is reasonable", 21, 11, 4)
    m("Karan", "who's paying May?", 21, 12, 7)
    m("Priya", "I'll start since I initiated. rest follow from June 1st", 21, 15, 3)

    # Casual filler
    sub_fillers = [
        ("password change karenge kabhi", "Meera"),
        ("otp bhej do koi", "Rohan"),
        ("billing cycle kab shuru hota hai", "Vikram"),
        ("annual vs monthly comparison", "Amit"),
        ("extra account sharing with roommate?", "Sneha"),
        ("what if one person leaves the group", "Anjali"),
        ("can we pause Spotify for 1 month?", "Karan"),
        ("Netflix recommendations algo is good", "Priya"),
        ("family sharing settings ka kya scene", "Meera"),
        ("cancel button kabhi dabayenge refund ke liye?", "Rohan"),
    ]
    for i, (txt, sender) in enumerate(sub_fillers):
        m(sender, txt, 22 + i, random.randint(8, 22), random.randint(0, 59))

    while len(msgs) < 75:
        sender = random.choice(p)
        m(sender, random.choice(GENERAL_TEMPLATES), random.randint(22, 25),
          random.randint(8, 22), random.randint(0, 59))

    msgs.sort(key=lambda x: x["timestamp"])
    dec_idx = next((i for i, x in enumerate(msgs)
                     if "subscription plan final" in x["text"].lower()), None)
    return msgs, dec_idx



# ── General chat generation ────────────────────────────────────────────

def gen_general_chat():
    """Generate ~3700 general chat messages across 6 months."""
    all_msgs = []

    months = [
        ("2024-01-01", "2024-01-31"),
        ("2024-02-01", "2024-02-28"),
        ("2024-03-01", "2024-03-31"),
        ("2024-04-01", "2024-04-30"),
        ("2024-05-01", "2024-05-31"),
        ("2024-06-01", "2024-06-30"),
    ]

    monthly_targets = [640, 590, 740, 540, 760, 680]

    for (start_str, end_str), target in zip(months, monthly_targets):
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")

        for _ in range(target):
            all_msgs.append(make_general_msg((start_dt, end_dt)))

    return all_msgs



# ── Dataset assembly ──────────────────────────────────────────────────

def generate_dataset():
    """Generate the complete dataset and return (messages, thread_info)."""
    thread1_start = datetime(2024, 5, 10, 18, 0, 0)
    thread2_start = datetime(2024, 3, 10, 19, 0, 0)
    thread3_start = datetime(2024, 4, 15, 11, 0, 0)

    manali_msgs, manali_dec = gen_manali_thread(thread1_start)
    party_msgs, party_dec = gen_house_party_thread(thread2_start)
    sub_msgs, sub_dec = gen_subscription_thread(thread3_start)

    general_msgs = gen_general_chat()

    all_msgs = general_msgs + manali_msgs + party_msgs + sub_msgs
    all_msgs.sort(key=lambda m: m["timestamp"])

    for i, msg in enumerate(all_msgs):
        msg["message_id"] = i + 1

    ordered = []
    for msg in all_msgs:
        ordered.append({
            "message_id": msg["message_id"],
            "sender": msg["sender"],
            "timestamp": msg["timestamp"].isoformat(),
            "text": msg["text"],
            "month": msg["month"],
            "thread_id": msg["thread_id"],
        })

    thread_info = {
        "thread_manali_trip": {
            "start_date": thread1_start.isoformat(),
            "message_count": len(manali_msgs),
            "decision_message_id": manali_msgs[manali_dec]["message_id"] if manali_dec is not None else None,
            "decision_text": manali_msgs[manali_dec]["text"] if manali_dec is not None else None,
        },
        "thread_house_party": {
            "start_date": thread2_start.isoformat(),
            "message_count": len(party_msgs),
            "decision_message_id": party_msgs[party_dec]["message_id"] if party_dec is not None else None,
            "decision_text": party_msgs[party_dec]["text"] if party_dec is not None else None,
        },
        "thread_subscription": {
            "start_date": thread3_start.isoformat(),
            "message_count": len(sub_msgs),
            "decision_message_id": sub_msgs[sub_dec]["message_id"] if sub_dec is not None else None,
            "decision_text": sub_msgs[sub_dec]["text"] if sub_dec is not None else None,
        },
    }

    return ordered, thread_info


# ── Validation ─────────────────────────────────────────────────────────

def validate(messages, thread_info):
    checks = {}
    checks["total_messages >= 4000"] = len(messages) >= 4000
    checks["exactly 8 participants"] = len(set(m["sender"] for m in messages)) == 8
    months = set(m["month"] for m in messages)
    checks["all six months present"] = months == {
        "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"}

    ids = [m["message_id"] for m in messages]
    checks["message_ids unique"] = len(ids) == len(set(ids))
    checks["message_ids sequential"] = ids == list(range(1, len(messages) + 1))

    try:
        for m in messages:
            datetime.fromisoformat(m["timestamp"])
        checks["timestamps valid"] = True
    except ValueError:
        checks["timestamps valid"] = False

    for key in ["thread_manali_trip", "thread_house_party", "thread_subscription"]:
        info = thread_info[key]
        checks[f"{key} exists ({info['message_count']} msgs)"] = info["message_count"] > 0
        checks[f"{key} has decision"] = info["decision_message_id"] is not None

    hinglish_words = ["kya", "haan", "nahi", "bhai", "kal", "karo", "hai", "kitna",
                      "acha", "theek", "scene", "pakka", "matlab", "yaar", "dekh"]
    short_msgs = [m for m in messages if len(m["text"].split()) <= 2]
    emoji_msgs = [m for m in messages if any(ord(c) > 0x1F000 for c in m["text"])]
    fwd_msgs = [m for m in messages if m["text"].lower().startswith("forwarded")
                or m["text"].lower().startswith("fwd:")]
    hinglish_msgs = [m for m in messages
                     if sum(w.lower() in hinglish_words for w in m["text"].split()) >= 1]

    checks["hinglish/code-mixed messages present"] = len(hinglish_msgs) > 500
    checks["short messages present"] = len(short_msgs) > 100
    checks["emoji messages present"] = len(emoji_msgs) > 100
    checks["forwarded messages present"] = len(fwd_msgs) > 10

    print("\n=== VALIDATION REPORT ===")
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    passed = sum(checks.values())
    print(f"  => {passed}/{len(checks)} checks passed")
    return all(checks.values())


# ── MongoDB insertion ──────────────────────────────────────────────────

def insert_into_mongodb(messages):
    from pymongo import MongoClient
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "group_chat_search")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[db_name]
    db.messages.delete_many({"message_id": {"$exists": True}})
    db.messages.insert_many(messages)
    count = db.messages.count_documents({})
    print(f"MongoDB: inserted {count} documents into {db_name}.messages")
    client.close()
    return count


# ── Entry point ────────────────────────────────────────────────────────

def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Generating dataset...")
    messages, thread_info = generate_dataset()

    with open(os.path.join(data_dir, "chat_messages.json"), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=1)

    senders = {}
    for m in messages:
        senders[m["sender"]] = senders.get(m["sender"], 0) + 1
    months = sorted(set(m["month"] for m in messages))
    stats = {
        "total_messages": len(messages),
        "participants": senders,
        "date_start": messages[0]["timestamp"],
        "date_end": messages[-1]["timestamp"],
        "months": months,
        "threads": thread_info,
    }
    with open(os.path.join(data_dir, "dataset_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    ok = validate(messages, thread_info)

    print("\nInserting into MongoDB...")
    try:
        insert_into_mongodb(messages)
    except Exception as e:
        print(f"MongoDB insertion FAILED: {e}")
        ok = False

    print("\nDONE" if ok else "\nCOMPLETED WITH FAILURES")


if __name__ == "__main__":
    main()

