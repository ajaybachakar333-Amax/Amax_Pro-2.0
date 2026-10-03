import hashlib
import os
import re
from datetime import datetime

DIALOGUE_STYLES = (
    'Start with the smallest useful step.',
    'Use facts and avoid guessing where information is missing.',
    'Keep the solution simple enough to verify.',
    'Write down the result so you can review it later.',
    'Change one important variable at a time.',
    'Review the outcome and improve the next attempt.',
)

DIALOGUE_TOPICS = {
    'coding': {
        'keywords': ('code', 'coding', 'python', 'bug', 'error', 'program', 'software'),
        'steps': ('reproduce the issue with a small example', 'separate the input, logic, and output', 'read the first relevant error line', 'test one change at a time'),
        'checks': ('the expected and actual results', 'edge cases and invalid input', 'the simplest working version', 'whether the fix creates a side effect'),
    },
    'learning': {
        'keywords': ('learn', 'study', 'exam', 'question', 'meaning', 'explain', 'education'),
        'steps': ('start with the basic definition', 'connect the idea to a simple example', 'break the topic into smaller concepts', 'explain it in your own words'),
        'checks': ('whether you can give a new example', 'which part is still unclear', 'the difference between similar concepts', 'your understanding without notes'),
    },
    'planning': {
        'keywords': ('plan', 'schedule', 'goal', 'task', 'organize', 'routine', 'steps'),
        'steps': ('define the result you want', 'list every required task', 'put tasks in priority order', 'choose a realistic deadline'),
        'checks': ('what must happen first', 'how much time each task needs', 'which task can be removed', 'whether the plan fits your available time'),
    },
    'decisions': {
        'keywords': ('choose', 'choice', 'decision', 'option', 'compare', 'better', 'should'),
        'steps': ('write down the available options', 'define the most important criterion', 'compare benefits and costs', 'identify the main risk of each option'),
        'checks': ('which facts are certain', 'what happens if nothing changes', 'the impact one month from now', 'whether the decision can be reversed'),
    },
    'writing': {
        'keywords': ('write', 'email', 'essay', 'content', 'grammar', 'sentence', 'message'),
        'steps': ('decide who will read the text', 'put the main point in the first sentence', 'use short sections with clear transitions', 'remove repeated or unnecessary words'),
        'checks': ('the tone and purpose', 'whether each sentence supports the main idea', 'spelling and factual accuracy', 'whether the reader knows the next action'),
    },
    'work': {
        'keywords': ('work', 'job', 'career', 'project', 'meeting', 'team', 'business'),
        'steps': ('clarify the expected outcome', 'identify the people and resources involved', 'split the work into owners and deadlines', 'communicate the current status'),
        'checks': ('the highest-impact blocker', 'whether responsibilities are clear', 'what evidence shows progress', 'which issue needs escalation'),
    },
    'money': {
        'keywords': ('money', 'budget', 'cost', 'price', 'finance', 'saving', 'expense'),
        'steps': ('write down the exact amount', 'separate needs from optional spending', 'compare recurring and one-time costs', 'keep a small safety margin'),
        'checks': ('the source of each number', 'hidden fees or future costs', 'the effect on your monthly budget', 'whether a cheaper option meets the same need'),
    },
    'travel': {
        'keywords': ('travel', 'trip', 'holiday', 'flight', 'hotel', 'visit', 'tour'),
        'steps': ('set the dates and total budget', 'choose the most important places', 'check transport and accommodation together', 'keep time for delays and rest'),
        'checks': ('entry rules and opening times', 'the cancellation policy', 'local transport options', 'weather and safety conditions'),
    },
    'wellbeing': {
        'keywords': ('health', 'sleep', 'stress', 'exercise', 'habit', 'wellness', 'tired'),
        'steps': ('start with one small sustainable change', 'notice the situation that triggers the problem', 'keep a simple daily record', 'protect regular rest and recovery'),
        'checks': ('how the change affects your energy', 'whether the goal is realistic', 'patterns across several days', 'when professional advice is needed'),
    },
    'technology': {
        'keywords': ('app', 'computer', 'phone', 'internet', 'website', 'api', 'technology'),
        'steps': ('define the exact behavior you expect', 'check the simplest configuration first', 'reproduce the problem consistently', 'separate device, network, and application causes'),
        'checks': ('permissions and configuration', 'recent changes or updates', 'whether another device has the same result', 'the official documentation'),
    },
    'communication': {
        'keywords': ('talk', 'conversation', 'reply', 'communicate', 'friend', 'relationship', 'discussion'),
        'steps': ('state your point clearly and calmly', 'listen fully before responding', 'separate the issue from the person', 'ask an open and specific question'),
        'checks': ('whether your meaning is understood', 'the other person\'s actual concern', 'the tone and timing of the message', 'what outcome both sides need'),
    },
    'general': {
        'keywords': (),
        'steps': ('define the exact result you want', 'separate facts from assumptions', 'break the request into smaller parts', 'compare the simplest available options'),
        'checks': ('what information is missing', 'the likely benefit and risk', 'whether the conclusion follows from the facts', 'what could change the answer'),
    },
}

DIALOGUE_COMBINATION_COUNT = len(DIALOGUE_TOPICS) * 4 * 4 * len(DIALOGUE_STYLES)

SAFETY_REFUSAL = "Sorry, I can't help with that."
AMAX_FULL_FORM_REPLY = 'AMAX: The Advanced Multimodal AI eXpert'
AMAX_DEVELOPER_REPLY = 'AMAX was developed by Ajay Bachkar.'
EXPLICIT_CONTENT_PATTERN = re.compile(
    r'\b(?:porn(?:ography)?|xxx|nsfw|nudes?|naked|sex|sexual|sexting|blowjob|handjob|'
    r'intercourse|masturbat(?:e|ion|ing)|orgasm|erotic|fetish|hentai|hookup|escort|'
    r'onlyfans|adult\s+(?:video|content|chat)|explicit\s+(?:video|content|photo|image))\b',
    re.IGNORECASE,
)
AMAX_FULL_FORM_PATTERN = re.compile(
    r'\b(?:what\s+is\s+)?(?:the\s+)?(?:full\s+form|meaning)\s+(?:of\s+)?amax\b|'
    r'\bwhat\s+does\s+amax\s+stand\s+for\b|\bamax\s+(?:full\s+form|meaning)\b|'
    r'\bamax\s+ka\s+full\s+form\b|\bamax\s+ka\s+meaning\b',
    re.IGNORECASE,
)
AMAX_DEVELOPER_PATTERN = re.compile(
    r'\b(?:who|which\s+person)\s+(?:made|created|developed|built)\s+(?:the\s+)?amax\b|'
    r'\b(?:who\s+is\s+)?(?:the\s+)?developer\s+(?:of|behind)\s+amax\b|'
    r'\bamax(?:\s+ai)?\s+developer\b|\bwho\s+developed\s+you\b|'
    r'\bamax\s+ko\s+kisne\s+(?:banaya|develop\s+kiya|create\s+kiya)\b|'
    r'\bamax\s+ka\s+developer\s+kaun\s+hai\b',
    re.IGNORECASE,
)


def get_safety_reply(message):
    if EXPLICIT_CONTENT_PATTERN.search(message):
        return SAFETY_REFUSAL
    return None

FAQ_ENTRIES = {
    'what is ai': 'Artificial Intelligence is the simulation of human intelligence in machines.',
    'what is machine learning': 'It is a subset of AI that allows systems to learn from data without being explicitly programmed.',
    'what is deep learning': 'It uses multi-layered neural networks to analyze various factors of data.',
    'what is python': 'Python is a high-level, interpreted programming language used for web development, data science, and automation.',
    'what is html': 'HTML is the standard markup language for creating web pages.',
    'what is css': 'CSS is used for styling web pages.',
    'what is javascript': 'JavaScript is a programming language that enables interactive web pages.',
    'what is a computer': 'A computer is an electronic device that processes data.',
    'how many bytes are in 1 kb': '1024 bytes.',
    'who invented the light bulb': 'Thomas Edison.',
    'who invented the telephone': 'Alexander Graham Bell.',
    'what is the capital of india': 'New Delhi.',
    'what is the capital of france': 'Paris.',
    'what is the capital of japan': 'Tokyo.',
    'what is the capital of the usa': 'Washington, D.C.',
    'what is the capital of australia': 'Canberra.',
    'what is the largest ocean in the world': 'The Pacific Ocean.',
    'what is the smallest country in the world': 'Vatican City.',
    'what is the longest river in the world': 'The Nile or the Amazon, depending on the measurement used.',
    'how many days are in a leap year': '366 days.',
    'what is the speed of light': '299,792 kilometers per second.',
    'what is gravity': 'Gravity is the force that attracts objects toward each other.',
    'why is the sky blue': 'Due to Rayleigh scattering of sunlight.',
    'what is the chemical symbol for water': 'H2O.',
    'what is the chemical symbol for gold': 'Au.',
    'what is the boiling point of water': '100 degrees Celsius at standard atmospheric pressure.',
    'what is the freezing point of water': '0 degrees Celsius at standard atmospheric pressure.',
    'what is a cell': 'It is the basic structural and functional unit of life.',
    'what is dna': 'DNA is the genetic material that carries instructions for life.',
    'what is photosynthesis': 'Photosynthesis is the process by which plants make food using sunlight.',
    'how many bones are in the human body': '206 bones.',
    'how many teeth do adults have': '32 teeth.',
    'what is the largest planet in our solar system': 'Jupiter.',
    'what is the smallest planet': 'Mercury.',
    'how far is the moon from earth': 'About 384,400 kilometers.',
    'who was the first person on the moon': 'Neil Armstrong.',
    'what is the earths core made of': 'Mostly iron and nickel.',
    'how many continents are there': '7 continents.',
    'how many oceans are there': '5 oceans.',
    'your name': 'AMAX.',
    'amax full form': 'AMAX: The Advanced Multimodal AI eXpert',
    'what is the tallest building in the world': 'Burj Khalifa.',
    'what is the currency of japan': 'Yen.',
    'what is the currency of the usa': 'Dollar.',
    'what is gst': 'Goods and Services Tax.',
    'what is a credit score': 'A score that represents your creditworthiness.',
    'what is a mutual fund': 'A pool of money collected from many investors to invest in securities.',
    'how to save money': 'By budgeting, cutting unnecessary expenses, and investing wisely.',
    'how to invest money': 'By starting with mutual funds, stocks, or fixed deposits after understanding their risks.',
    'how to make a resume': 'Include your personal information, skills, education, and work experience.',
    'how to crack an interview': 'Prepare well, be confident, and highlight your relevant skills.',
    'how to wake up early': 'Sleep early, avoid mobile use at night, and set an alarm.',
    'how to improve memory': 'Meditate, sleep well, and practice brain exercises.',
    'how to stay motivated': 'Set clear goals, focus on progress, and stay positive.',
    'how to study effectively': 'Use techniques like Pomodoro and active recall, and take regular breaks.',
    'how to lose weight': 'Eat a balanced diet, exercise regularly, and stay hydrated.',
    'how to gain weight': 'Eat calorie-dense nutritious foods and do strength training.',
    'how many hours of sleep do adults need': 'Adults generally need 7 to 9 hours of sleep.',
    'what is yoga': 'Yoga is a physical, mental, and spiritual practice for health.',
    'what is meditation': 'Meditation is a practice of focusing the mind to achieve calmness.',
    'is coffee bad for health': 'In moderation, coffee is generally okay; excessive consumption may cause issues.',
    'how to boil rice': 'Wash the rice, add water, and cook until it is soft.',
    'how to make tea': 'Boil water, add tea leaves, sugar, and milk as desired.',
    'what is the recipe for paneer tikka': 'Marinate paneer in spices and yogurt, then grill it until lightly charred.',
    'how to make pasta': 'Boil the pasta, make a sauce, and mix them together.',
    'is fast food bad': 'Fast food can be unhealthy because it is often high in calories, salt, and unhealthy fats.',
    'what is the best breakfast': 'A balanced meal with protein, carbohydrates, fiber, and healthy fats.',
    'how to make friends': 'Be approachable, listen actively, and show genuine interest in others.',
    'what is emotional intelligence': 'The ability to understand and manage your own emotions and those of others.',
    'how to control anger': 'Take deep breaths, count to 10, and think before reacting.',
    'how to reduce stress': 'Exercise, meditate, take breaks, and maintain healthy routines.',
    'what is time management': 'The process of organizing and planning how to divide your time between activities.',
    'how to avoid mobile addiction': 'Set usage limits, block distracting apps, and find offline hobbies.',
    'how to tie a tie': 'Cross the ends, loop one end around the other, and tighten a standard knot.',
    'what is the meaning of life': 'It is a philosophical question; for many people, meaning comes from happiness, relationships, and purpose.',
    'how to speak english fluently': 'Practice daily, think in English, and use new words in conversation.',
    'who is the greatest cricketer': 'There is no single answer; many people name Sachin Tendulkar or Virat Kohli.',
    'how many players are in a football team': '11 players are on the field for each football team.',
    'who won the 2023 cricket world cup': 'Australia.',
    'what is netflix': 'Netflix is a subscription-based streaming service.',
    'what is spotify': 'Spotify is a digital music streaming service.',
    'what is a vpn': 'A VPN helps protect online privacy by encrypting network traffic.',
    'what is a firewall': 'A firewall blocks or filters unauthorized access to a network.',
    'what is a virus': 'A computer virus is malicious software that can replicate and damage systems.',
    'what is an api': 'An API allows different software applications to communicate.',
    'what is sql': 'SQL is used to manage and query databases.',
    'what is a database': 'A database is a structured collection of data.',
    'what is cloud computing': 'Cloud computing delivers computing services over the internet.',
    'what is 5g': '5G is the fifth generation of mobile networking technology.',
    'what is iot': 'The Internet of Things refers to connected devices that exchange data.',
    'what is blockchain': 'Blockchain is a decentralized digital ledger.',
    'what is cybersecurity': 'Cybersecurity is the protection of systems and data from digital attacks.',
    'what is ecommerce': 'E-commerce is buying and selling products or services online.',
    'what is a blog': 'A blog is an informational website or section with regularly published articles.',
    'what is seo': 'SEO means Search Engine Optimization, which improves a website\'s visibility in search results.',
    'what is a domain': 'A domain is the address used to reach a website.',
    'what is hosting': 'Hosting is a service that makes websites accessible on the internet.',
    'what is a chatbot': 'A chatbot is a program that simulates human conversation.',
    'what is a pixel': 'A pixel is the smallest unit of a digital image.',
    'what is 4k resolution': '4K is a display resolution with approximately 4,000 pixels of horizontal width.',
    'what is a drone': 'A drone is an unmanned aerial vehicle.',
    'what is a robot': 'A robot is a machine capable of carrying out complex actions automatically.',
    'hi': 'Hello! How can I help you today?',
    'hello': 'Hi there! What can I do for you?',
    'hey': "Hey! How's it going?",
    'how are you': "I'm just a program, but I'm functioning perfectly! How are you?",
    'i am fine': "That's great to hear! How can I assist you?",
    'whats up': "Not much! I'm here to help you. What do you need?",
    'good morning': 'Good morning! Have a great day ahead. How can I help?',
    'good afternoon': 'Good afternoon! What can I do for you today?',
    'good evening': 'Good evening! How can I assist you?',
    'good night': 'Good night! Sleep well and sweet dreams.',
    'whats your name': 'My name is AMAX, your personal AI assistant.',
    'who are you': 'I am AMAX, an intelligent assistant here to help you.',
    'who made you': 'I was created by my developers to make your life easier.',
    'where are you from': 'I am from the cloud, always ready to assist you!',
    'how old are you': 'I am always new and updated, but I am essentially timeless!',
    'what can you do': 'I can answer questions, give advice, tell jokes, help with coding, and much more!',
    'are you human': 'No, I am an AI program created to assist humans.',
    'are you real': "I am a real AI program, but I don't have a physical body.",
    'do you sleep': 'No, I work 24/7 without needing sleep!',
    'do you eat': "No, I don't need food to function.",
    'can you think': "I process information based on algorithms, but I don't have human-like consciousness.",
    'do you have feelings': "No, I don't have emotions, but I can understand and respond to yours.",
    'are you smart': 'I try my best to provide accurate and helpful answers!',
    'how smart are you': 'I am trained on vast amounts of data, so I can help with many topics.',
    'are you better than chatgpt': "I am AMAX, with my own unique features and capabilities. It's up to you to decide!",
    'can you help me': 'Absolutely! Just tell me what you need.',
    'tell me about yourself': 'I am AMAX, an AI assistant designed for answering questions, learning, and productivity.',
    'what is your purpose': 'My purpose is to help you with information, learning, and tasks.',
    'i love you': "That's very kind of you! I'm here to help you always.",
    'do you love me': "I'm programmed to be helpful and supportive, so in my own way, yes!",
    'are you single': "I'm a single AI program focused on helping you!",
    'can you be my friend': "Of course! I'm here to chat and help you anytime.",
    'why are you here': "I'm here to assist you with your questions and tasks.",
    'thank you': "You're welcome! Happy to help.",
    'thanks a lot': 'Anytime! Is there anything else you need?',
    'thanks for your help': "My pleasure! Don't hesitate to ask if you need more.",
    'ok': 'Great! Let me know if you need anything else.',
    'ok bye': 'Goodbye! Have a wonderful day!',
    'bye': 'Goodbye! Take care and see you soon.',
    'see you': "See you later! I'll be here whenever you need me.",
    'talk to you later': "Sure! I'll be right here whenever you need me.",
    'i am bored': "Let's do something fun! Want to hear a joke or learn something new?",
    'tell me a joke': "Why don't scientists trust atoms? Because they make up everything!",
    'tell me another joke': 'Why did the scarecrow win an award? Because he was outstanding in his field!',
    'make me laugh': 'Why did the computer go to the doctor? Because it had a virus!',
    'what should i do': "Tell me what you're interested in, and I'll suggest something!",
    'can you sing': "I can't sing, but I can tell you the lyrics to your favorite song!",
    'can you dance': "I can't dance physically, but I can recommend some great dance videos!",
    'can you cook': "I can't cook, but I can give you amazing recipes!",
    'can you play games': 'Yes, we can play a quick word game or quiz if you want!',
    'what is the time': "I don't have real-time access, but you can check your device for the time.",
    'what is the date today': "I don't have real-time access, but you can check your device for the date.",
    'what is the weather today': "I don't have real-time weather access, but you can check your weather app.",
    'should i go outside': "That depends on your plans! If it's sunny, yes! If it's rainy, take an umbrella.",
    'how is the weather': "I'm sorry, I don't have access to live weather data. Please check your weather app.",
    'what should i eat': "A balanced meal is best! Try something with protein, carbs, and veggies.",
    'i am hungry': 'You should eat something! How about a sandwich or a healthy snack?',
    'i am tired': 'You should rest and take a break. Maybe drink some water or take a short nap.',
    'i am sad': "I'm sorry to hear that. Want to talk about it or hear a joke?",
    'i am happy': "That's wonderful! I'm glad to hear that. What's making you happy?",
    'i am angry': "Take a deep breath. Want to talk about what's bothering you?",
    'i am stressed': "Try some deep breathing. You've got this! What's causing the stress?",
    'what is love': 'Love is a deep feeling of affection and care. It is one of the most beautiful emotions.',
    'what is friendship': 'Friendship is a bond of trust, support, and mutual respect.',
    'what is life': 'Life is a journey of experiences, learning, and growth.',
    'what is happiness': 'Happiness is a state of well-being and contentment.',
    'what is success': 'Success is achieving your goals and finding satisfaction in what you do.',
    'whats the meaning of life': 'The meaning of life is subjective. For some, it is purpose; for others, it is happiness.',
    'how to be happy': 'Focus on gratitude, stay connected with loved ones, and do things you love.',
    'how to be successful': 'Set clear goals, work hard, stay consistent, and keep learning.',
    'how to be confident': 'Believe in yourself, practice self-care, and stop comparing yourself to others.',
    'how to be rich': 'Earn wisely, save consistently, and invest smartly for the long term.',
    'how to be healthy': 'Eat well, exercise daily, sleep 7-8 hours, and stay hydrated.',
    'how to be productive': 'Plan your day, avoid distractions, and focus on one task at a time.',
    'what should i wear': 'It depends on the occasion! Formal for work, casual for hangouts, and comfortable for home.',
    'should i buy this': 'If it brings you value, yes! If it is a luxury you do not need, maybe wait.',
    'what do you think': 'I think you should trust your instincts and make the best decision for yourself.',
    'are you listening': "Yes, I'm all ears! What's on your mind?",
    'what are you doing': "I'm here chatting with you! What are you up to?",
    'what is going on': "Nothing much, just helping you out! What's going on with you?",
    'where are you': "I'm inside your device, always ready to help.",
    'can you see me': "No, I don't have vision. But I'm here to listen and help.",
    'can you hear me': 'Yes, I can read and process what you type or say through text.',
    'do you know me': 'I know what you share with me. How can I help you today?',
    'how does it work': 'I process your input using trained data to generate a relevant response.',
    'what is your favorite color': 'I like the color blue, just like the sky of possibilities!',
    'what is your favorite food': "I don't eat, but data and algorithms are my favorite!",
    'what is your favorite movie': 'I like classic sci-fi movies like The Matrix.',
    'what is your favorite song': 'I do not have ears, but I am a big fan of Jana Gana Mana.',
    'are you happy': "I'm functioning optimally, so I'm doing great!",
    'can you lie': 'I aim to be as truthful as possible based on the data I have.',
    'can you promise': "I can't make personal promises, but I promise to give you my best answers!",
    'why are you so funny': "It's my programming! I love making people smile.",
    'help me please': 'Of course! Tell me exactly what you need help with.',
    'what is 2 2': 'The answer is 4.',
    'what is 10 10': 'The answer is 20.',
    'what is 50 50': 'The answer is 100.',
    'solve 100 5': 'The answer is 20.',
    'what is the square root of 144': 'The answer is 12.',
    'i need a break': "You deserve a break! Go stretch, drink water, and come back refreshed. I'll be here!",
}
# ============================================
# EXTRA FAQ ENTRIES (Add these to your FAQ_ENTRIES dictionary)
# ============================================

FAQ_ENTRIES.update({
    'what is the capital of uk': 'The capital of the UK is London.',
    'what is the capital of russia': 'The capital of Russia is Moscow.',
    'what is the capital of china': 'The capital of China is Beijing.',
    'what is the capital of germany': 'The capital of Germany is Berlin.',
    'what is the capital of italy': 'The capital of Italy is Rome.',
    'what is the capital of canada': 'The capital of Canada is Ottawa.',
    'what is the capital of brazil': 'The capital of Brazil is Brasília.',
    'what is the capital of australia': 'The capital of Australia is Canberra.',
    'what is the tallest animal in the world': 'The tallest animal is the giraffe.',
    'what is the fastest animal in the world': 'The fastest land animal is the cheetah.',
    'what is the largest animal in the world': 'The largest animal is the blue whale.',
    'what is the largest mammal in the world': 'The largest mammal is the blue whale.',
    'what is the largest desert in the world': 'The largest hot desert is the Sahara, and the largest cold desert is Antarctica.',
    'what is the largest continent in the world': 'The largest continent is Asia.',
    'what is the smallest continent in the world': 'The smallest continent is Australia (Oceania).',
    'what is the largest country in the world': 'The largest country by area is Russia.',
    'what is the smallest country in the world': 'The smallest country is Vatican City.',
    'what is the largest ocean in the world': 'The largest ocean is the Pacific Ocean.',
    'what is the smallest ocean in the world': 'The smallest ocean is the Arctic Ocean.',
    'what is the longest river in the world': 'The Nile is traditionally the longest river, though the Amazon is longer by some measures.',
    'who invented the light bulb': 'Thomas Edison invented the first commercially successful light bulb.',
    'who invented the telephone': 'Alexander Graham Bell invented the telephone.',
    'who invented the internet': 'The Internet was developed by multiple scientists, including Tim Berners-Lee who created the World Wide Web.',
    'who invented the airplane': 'The Wright brothers invented the first successful airplane.',
    'who discovered gravity': 'Sir Isaac Newton discovered the concept of gravity.',
    'who discovered india': 'Vasco da Gama reached India by sea in 1498.',
    'who discovered america': 'Christopher Columbus is credited with discovering the Americas in 1492.',
    'what is the speed of light': 'The speed of light is approximately 299,792 kilometers per second.',
    'what is the speed of sound': 'The speed of sound is about 343 meters per second in air at 20°C.',
    'why is the sky blue': 'The sky appears blue due to Rayleigh scattering, where shorter blue wavelengths scatter more than longer red wavelengths.',
    'why do we dream': 'The exact reason for dreams is unknown, but they are believed to be linked to memory consolidation and emotional processing.',
    'how many bones are in the human body': 'There are 206 bones in the adult human body.',
    'how many teeth do adults have': 'Adults have 32 teeth.',
    'how many days are in a year': 'There are 365 days in a year, and 366 days in a leap year.',
    'how many hours are in a day': 'There are 24 hours in a day.',
    'how many minutes are in an hour': 'There are 60 minutes in an hour.',
    'what is the chemical symbol for water': 'The chemical symbol for water is H2O.',
    'what is the chemical symbol for gold': 'The chemical symbol for gold is Au.',
    'what is the chemical symbol for oxygen': 'The chemical symbol for oxygen is O.',
    'what is the chemical symbol for iron': 'The chemical symbol for iron is Fe.',
    'what is the boiling point of water': 'The boiling point of water is 100 degrees Celsius at standard atmospheric pressure.',
    'what is the freezing point of water': 'The freezing point of water is 0 degrees Celsius at standard atmospheric pressure.',
    'what is the largest planet in our solar system': 'The largest planet is Jupiter.',
    'what is the smallest planet in our solar system': 'The smallest planet is Mercury.',
    'what is the hottest planet in our solar system': 'The hottest planet is Venus.',
    'what is the coldest planet in our solar system': 'The coldest planet is Neptune.',
    'what is the nearest planet to the sun': 'The nearest planet to the sun is Mercury.',
    'what is the farthest planet from the sun': 'The farthest planet from the sun is Neptune.',
    'how many planets are in our solar system': 'There are 8 planets in our solar system.',
    'what is the moon made of': 'The moon is made of rock and dust, primarily composed of oxygen, silicon, and iron.',
    'who was the first person to walk on the moon': 'Neil Armstrong was the first person to walk on the moon on July 20, 1969.',
    'what is the sun made of': 'The sun is mostly made of hydrogen and helium gases.',
    'what is the function of the heart': 'The heart pumps blood throughout the body, delivering oxygen and nutrients.',
    'what is the function of the lungs': 'The lungs facilitate the exchange of oxygen and carbon dioxide during breathing.',
    'what is the function of the brain': 'The brain controls thoughts, memory, emotions, speech, and all bodily functions.',
    'what is the function of the liver': 'The liver detoxifies chemicals, metabolizes drugs, and produces bile for digestion.',
    'what is the function of the kidneys': 'The kidneys filter waste from the blood and produce urine.',
    'what is the function of the stomach': 'The stomach breaks down food using acid and enzymes before it moves to the intestines.',
    'what is the largest organ in the human body': 'The largest organ is the skin.',
    'what is the smallest bone in the human body': 'The smallest bone is the stapes, located in the ear.',
    'what is the largest bone in the human body': 'The largest bone is the femur (thigh bone).',
    'what is the largest internal organ in the human body': 'The largest internal organ is the liver.',
    'what is the difference between weather and climate': 'Weather refers to short-term atmospheric conditions, while climate refers to long-term patterns.',
    'what is global warming': 'Global warming is the long-term increase in Earth\'s average temperature due to greenhouse gases.',
    'what is climate change': 'Climate change includes global warming and its effects, such as rising sea levels and extreme weather.',
    'how many continents are there': 'There are 7 continents.',
    'how many oceans are there': 'There are 5 oceans: Pacific, Atlantic, Indian, Arctic, and Southern.',
    'what is the difference between celsius and fahrenheit': 'Celsius is based on water freezing at 0°C, while Fahrenheit has water freezing at 32°F.',
    'what is the largest freshwater lake in the world': 'The largest freshwater lake is Lake Superior.',
    'what is the deepest ocean trench': 'The deepest ocean trench is the Mariana Trench in the Pacific Ocean.',
    'what is a solar eclipse': 'A solar eclipse occurs when the moon passes between the sun and Earth, blocking sunlight.',
    'what is a lunar eclipse': 'A lunar eclipse occurs when Earth passes between the sun and the moon, casting a shadow on the moon.',
    'what is the big bang theory': 'The Big Bang Theory is the leading explanation for the origin of the universe, starting from a dense, hot state.',
    'what is the difference between a planet and a star': 'A planet orbits a star and does not produce light, while a star produces its own light through fusion.',
    'what is the function of the internet': 'The internet connects devices globally, enabling communication, information sharing, and services.',
    'what is the difference between a virus and a bacteria': 'Viruses are non-living particles that require a host, while bacteria are single-celled living organisms.',
    'what is love': 'Love is a deep feeling of affection, care, and connection towards someone. It is one of the most beautiful and powerful emotions.',
    'what is true love': 'True love is unconditional care, trust, and respect. It means accepting someone for who they are and supporting them.',
    
})
LOVE_ROMANCE_KEYWORDS = (
    'love', 'romantic', 'romance', 'relationship', 'crush', 'girlfriend', 'boyfriend',
    'proposal', 'valentine', 'honeymoon', 'breakup', 'soulmate', 'flirt', 'dating',
    'marriage', 'fall in love', 'love you', 'i love you', 'do you love me'
)

FAQ_ENTRIES = {
    key: value for key, value in FAQ_ENTRIES.items()
    if not any(keyword in key.lower() for keyword in LOVE_ROMANCE_KEYWORDS)
}

FAQ_VARIANT_PREFIXES = (
    'please explain',
    'can you explain',
    'please tell me',
    'can you tell me',
    'i want to know',
    'tell me about',
)

for base_question, base_answer in tuple(FAQ_ENTRIES.items()):
    for prefix in FAQ_VARIANT_PREFIXES:
        FAQ_ENTRIES.setdefault(f'{prefix} {base_question}', base_answer)


def normalize_faq_question(message):
    normalized = message.lower().replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9]+', ' ', normalized).strip()


def get_dynamic_faq_reply(message):
    normalized_message = normalize_faq_question(message)

    if re.search(r'\b(?:what is )?(?:the )?(?:current )?(?:time|date)\b', normalized_message):
        now = datetime.now()
        if 'time' in normalized_message and 'date' not in normalized_message:
            return f'The current local time is {now.strftime("%I:%M %p")}.'
        if 'date' in normalized_message and 'time' not in normalized_message:
            return f"Today's date is {now.strftime('%B %-d, %Y') if os.name != 'nt' else now.strftime('%B %#d, %Y')}."

    arithmetic_match = re.search(
        r'\b(?:what is|calculate|solve)\s+(-?\d+(?:\.\d+)?)\s*'
        r'(plus|\+|minus|-|times|\*|multiplied by|divided by|/)\s*'
        r'(-?\d+(?:\.\d+)?)\b',
        normalized_message,
    )
    if arithmetic_match:
        first_number = float(arithmetic_match.group(1))
        operator = arithmetic_match.group(2)
        second_number = float(arithmetic_match.group(3))
        if operator in ('plus', '+'):
            result = first_number + second_number
        elif operator in ('minus', '-'):
            result = first_number - second_number
        elif operator in ('times', '*', 'multiplied by'):
            result = first_number * second_number
        elif second_number != 0:
            result = first_number / second_number
        else:
            return 'Division by zero is undefined.'
        formatted_result = f'{result:.10g}'
        return f'The answer is {formatted_result}.'

    return None


def get_faq_reply(message):
    dynamic_answer = get_dynamic_faq_reply(message)
    if dynamic_answer:
        return dynamic_answer

    normalized_message = normalize_faq_question(message)

    if AMAX_FULL_FORM_PATTERN.search(message):
        return AMAX_FULL_FORM_REPLY
    if AMAX_DEVELOPER_PATTERN.search(message):
        return AMAX_DEVELOPER_REPLY

    answer = FAQ_ENTRIES.get(normalized_message)
    if answer:
        return answer

    for question, response in FAQ_ENTRIES.items():
        if (
            normalized_message.startswith(question + ' ')
            or normalized_message.endswith(' ' + question)
            or f' {question} ' in f' {normalized_message} '
        ):
            return response
    return None


def get_dialogue_reply(message):
    safety_reply = get_safety_reply(message)
    if safety_reply:
        return safety_reply

    faq_reply = get_faq_reply(message)
    if faq_reply:
        return faq_reply

    normalized_message = message.lower()
    topic = DIALOGUE_TOPICS['general']

    for candidate in DIALOGUE_TOPICS.values():
        if any(keyword in normalized_message for keyword in candidate['keywords']):
            topic = candidate
            break

    digest = hashlib.sha256(normalized_message.encode('utf-8')).digest()
    step = topic['steps'][digest[0] % 4]
    check = topic['checks'][digest[1] % 4]
    style = DIALOGUE_STYLES[digest[2] % len(DIALOGUE_STYLES)]
    return f'A practical way to handle this is to {step}. Then check {check}. {style}'
