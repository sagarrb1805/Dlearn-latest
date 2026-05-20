import pandas as pd
resources_data = [
    {
        'ResourceID': 101,
        'Title': "Intro to Science",
        'Format': "Video",
        'Accessibility': ["ISL", "Captions", "Transcripts"],
        'DeafnessSuitability': "Mild",
        'CommunicationMode': ["Sign", "Speech"],
        'LearningStyles': {'Auditory': 0.2, 'Kinesthetic': 0.6, 'Read/Write': 0.4, 'Visual': 0.8}
    },
    {
        'ResourceID': 102,
        'Title': "Physics Simulation",
        'Format': "Interactive",
        'Accessibility': ["Captions"],
        'DeafnessSuitability': "Moderate",
        'CommunicationMode': ["Sign Supported Speech"],
        'LearningStyles': {'Auditory': 0.3, 'Kinesthetic': 0.9, 'Read/Write': 0.3, 'Visual': 0.7}
    },
    {
        'ResourceID': 103,
        'Title': "Mathematics Lecture",
        'Format': "Text",
        'Accessibility': ["Transcripts"],
        'DeafnessSuitability': "Profound",
        'CommunicationMode': ["Speech"],
        'LearningStyles': {'Auditory': 0.5, 'Kinesthetic': 0.3, 'Read/Write': 0.9, 'Visual': 0.2}
    },
    {
        'ResourceID': 104,
        'Title': "History Podcast",
        'Format': "Audio",
        'Accessibility': ["Voice"],
        'DeafnessSuitability': "Mild",
        'CommunicationMode': ["Speech"],
        'LearningStyles': {'Auditory': 0.9, 'Kinesthetic': 0.2, 'Read/Write': 0.5, 'Visual': 0.3}
    },
    {
        'ResourceID': 105,
        'Title': "Sign Language Basics",
        'Format': "Video",
        'Accessibility': ["ISL"],
        'DeafnessSuitability': "Severe",
        'CommunicationMode': ["Sign"],
        'LearningStyles': {'Auditory': 0.1, 'Kinesthetic': 0.5, 'Read/Write': 0.2, 'Visual': 0.9}
    },
    {
        'ResourceID': 106,
        'Title': "Chemistry Lab Experiments",
        'Format': "Interactive",
        'Accessibility': ["Captions", "Transcripts"],
        'DeafnessSuitability': "Moderate",
        'CommunicationMode': ["Sign Supported Speech", "Text"],
        'LearningStyles': {'Auditory': 0.2, 'Kinesthetic': 0.9, 'Read/Write': 0.4, 'Visual': 0.7}
    },
    {
        'ResourceID': 107,
        'Title': "World War Documentary",
        'Format': "Video",
        'Accessibility': ["Captions", "ISL"],
        'DeafnessSuitability': "Mild",
        'CommunicationMode': ["Sign", "Speech"],
        'LearningStyles': {'Auditory': 0.4, 'Kinesthetic': 0.3, 'Read/Write': 0.5, 'Visual': 0.8}
    },
    {
        'ResourceID': 108,
        'Title': "Programming Fundamentals",
        'Format': "Text",
        'Accessibility': ["Transcripts", "Braille"],
        'DeafnessSuitability': "Profound",
        'CommunicationMode': ["Text"],
        'LearningStyles': {'Auditory': 0.1, 'Kinesthetic': 0.2, 'Read/Write': 0.9, 'Visual': 0.4}
    },
    {
        'ResourceID': 109,
        'Title': "Astronomy for Beginners",
        'Format': "Video",
        'Accessibility': ["Captions", "Transcripts"],
        'DeafnessSuitability': "Severe",
        'CommunicationMode': ["Sign", "Speech"],
        'LearningStyles': {'Auditory': 0.3, 'Kinesthetic': 0.6, 'Read/Write': 0.5, 'Visual': 0.9}
    },
    {
        'ResourceID': 110,
        'Title': "Environmental Science Discussion",
        'Format': "Audio",
        'Accessibility': ["Captions"],
        'DeafnessSuitability': "Moderate",
        'CommunicationMode': ["Speech", "Text"],
        'LearningStyles': {'Auditory': 0.8, 'Kinesthetic': 0.2, 'Read/Write': 0.5, 'Visual': 0.4}
    },
    {
        'ResourceID': 111,
        'Title': "Mathematical Problem Solving",
        'Format': "Interactive",
        'Accessibility': ["Captions", "Braille"],
        'DeafnessSuitability': "Severe",
        'CommunicationMode': ["Text"],
        'LearningStyles': {'Auditory': 0.2, 'Kinesthetic': 0.8, 'Read/Write': 0.6, 'Visual': 0.5}
    },
    {
        'ResourceID': 112,
        'Title': "Shakespeare's Plays - Analysis",
        'Format': "Text",
        'Accessibility': ["Transcripts"],
        'DeafnessSuitability': "Profound",
        'CommunicationMode': ["Text"],
        'LearningStyles': {'Auditory': 0.3, 'Kinesthetic': 0.2, 'Read/Write': 0.9, 'Visual': 0.4}
    },
    {
        'ResourceID': 113,
        'Title': "Computer Vision with AI",
        'Format': "Video",
        'Accessibility': ["Captions"],
        'DeafnessSuitability': "Moderate",
        'CommunicationMode': ["Sign Supported Speech"],
        'LearningStyles': {'Auditory': 0.4, 'Kinesthetic': 0.3, 'Read/Write': 0.5, 'Visual': 0.9}
    },
    {
        'ResourceID': 114,
        'Title': "Geography of the World",
        'Format': "Interactive",
        'Accessibility': ["Captions", "ISL"],
        'DeafnessSuitability': "Mild",
        'CommunicationMode': ["Sign", "Speech"],
        'LearningStyles': {'Auditory': 0.3, 'Kinesthetic': 0.5, 'Read/Write': 0.4, 'Visual': 0.7}
    },
    {
        'ResourceID': 115,
        'Title': "Genetics and DNA",
        'Format': "Text",
        'Accessibility': ["Transcripts"],
        'DeafnessSuitability': "Profound",
        'CommunicationMode': ["Text"],
        'LearningStyles': {'Auditory': 0.2, 'Kinesthetic': 0.3, 'Read/Write': 0.9, 'Visual': 0.4}
    }
]


resources_df = pd.DataFrame(resources_data)

