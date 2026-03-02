# Smart 2D House Plan Generator

An intelligent web application that generates **customized 2D floor plans** for houses based on user-selected lifestyles and room dimensions.  
It uses algorithmic placement to create efficient layouts with connectivity checks and interactive visualizations.

---

##  Key Features

###  Lifestyle-Based Room Suggestions
Predefined room sets for different lifestyles:

- Work-from-Home  
- Family with Kids  
- Elderly-Friendly  
- Pet Owner  
- Minimalist  
- Entertainer  
- Remote Worker  
- Eco-Friendly  
- Hobbyist  
- Fitness Enthusiast  
- Multigenerational  
- Smart Home Lover  
- Social Butterfly  
- Accessibility Focused  

---

###  Custom Room Inputs
- Specify number of rooms  
- Define length and width (in feet)  
- Full control over layout requirements  

---

###  Multiple Plan Generation
- Generates up to **3 optimized floor plan options**  
- Random + rule-based intelligent placement  

---

###  Interactive 2D Visualization
Real-time canvas rendering showing:

- Colored rooms  
- Doors with swing directions  
- Gap distances (highlighted)  
- Plan boundaries  
- Total area  

---

###  Validation & Warnings
- Room connectivity checks (BFS-based)  
- Adjacency preference matching  
- Design rule validation  
  - No overlaps  
  - Proper entrances  
  - Minimum gaps  
  - Logical layout rules  

---

###  Export Options
- Download plans as **PNG images**  
- Ready for sharing or printing  

---

##  Tech Stack

### Frontend
- Flutter Web (Dart)

### Packages
- http (API communication)  
- path_provider (file export)  
- dart:ui (custom canvas painting)  
- dart:math (calculations & geometry)  

### Backend
- Flask (Python) with CORS support  

### Core Logic
- Room placement algorithms  
- Adjacency graphs  
- BFS connectivity checks  
- Door & gap detection  

---

##  Getting Started

###  Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

---

###  Frontend Setup

```bash
flutter pub get
flutter run -d chrome 
```

---

## 🎥 Demo

Watch the full demo video:  
Smart 2D House Plan Generator Demo  

---

## 📄 Documentation

Project Documentation Folder  
(Google Drive folder with detailed docs and images)

---

