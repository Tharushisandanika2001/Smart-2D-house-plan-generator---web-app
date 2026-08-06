# 🏠 Smart 2D House Plan Generator

An intelligent web application that generates customized **2D house floor plans** based on user-selected lifestyles, room requirements, and room dimensions.

The system uses intelligent rule-based room placement, connectivity validation, adjacency preferences, and interactive 2D visualization to generate practical house layouts.

---

## 🌟 Overview

The **Smart 2D House Plan Generator** helps users create customized house floor plans without manually designing the entire layout.

Users can:

* Select a lifestyle
* Get recommended rooms based on the selected lifestyle
* Enter custom room dimensions
* Generate multiple house plan options
* View plans interactively in 2D
* Check room connectivity and layout rules
* Download generated plans as images

The application consists of a **Flutter Web frontend** and a **Python Flask backend**.

---

## ✨ Key Features

### 🏡 Lifestyle-Based Room Suggestions

The application provides predefined room recommendations for different lifestyles:

* Work-from-Home
* Family with Kids
* Elderly-Friendly
* Pet Owner
* Minimalist
* Entertainer
* Remote Worker
* Eco-Friendly
* Hobbyist
* Fitness Enthusiast
* Multigenerational
* Smart Home Lover
* Social Butterfly
* Accessibility Focused

---

### 📐 Custom Room Dimensions

Users can define their own room requirements by specifying:

* Number of rooms
* Room names
* Room length
* Room width
* Layout requirements

This allows users to create plans based on their actual space requirements.

---

### 🧠 Intelligent Plan Generation

The system uses algorithmic and rule-based placement techniques to generate suitable floor plans.

It considers:

* Room placement
* Room adjacency
* Room connectivity
* Minimum gaps
* Entrance requirements
* Layout constraints
* Overlap prevention

The application can generate multiple optimized plan options for comparison.

---

### 🎨 Interactive 2D Visualization

Generated plans are displayed using an interactive 2D canvas.

The visualization includes:

* 🛏️ Rooms
* 🚪 Doors
* ↔️ Gap distances
* 📏 Plan boundaries
* 📊 Total floor area
* 🎨 Different room visualizations

---

### 🔍 Validation & Layout Checking

The system validates generated layouts using different rules and algorithms.

Validation includes:

* No room overlaps
* Room connectivity
* Minimum spacing
* Logical room placement
* Proper entrance placement
* Adjacency preference matching

A **BFS-based connectivity check** is used to verify that the rooms form a connected layout.

---

### 📥 Plan Export

Generated house plans can be exported as **PNG images** for:

* Sharing
* Saving
* Printing
* Further reference

---

## 🛠️ Technology Stack

### Frontend

* Flutter Web
* Dart
* Custom Canvas / `dart:ui`
* HTTP API communication

### Backend

* Python
* Flask
* Flask-CORS

### Core Algorithms

* Rule-based room placement
* Room adjacency graphs
* BFS connectivity checking
* Geometry calculations
* Door detection
* Gap detection
* Overlap validation

---

## 📁 Project Structure

```text
Smart-2D-house-plan-generator---web-app/
│
├── backend/
│   ├── app.py
│   └── requirements.txt
│
├── frontend/
│   ├── lib/
│   │   ├── main.dart
│   │   └── splash_page.dart
│   │
│   ├── assets/
│   │   └── background.jpg
│   │
│   ├── pubspec.yaml
│   └── ...
│
├── README.md
└── .gitignore
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Tharushisandanika2001/Smart-2D-house-plan-generator---web-app.git
```

Navigate into the project:

```bash
cd Smart-2D-house-plan-generator---web-app
```

---

## 🐍 Backend Setup

Navigate to the backend folder:

```bash
cd backend
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Start the Flask backend:

```bash
python app.py
```

The backend API will then be available through the configured Flask server.

---

## 💙 Flutter Web Setup

Open a new terminal and navigate to the Flutter project:

```bash
cd frontend
```

Install Flutter dependencies:

```bash
flutter pub get
```

Run the application in Chrome:

```bash
flutter run -d chrome
```

---

## 🔄 System Workflow

```text
User
  │
  ▼
Select Lifestyle
  │
  ▼
Recommended Rooms
  │
  ▼
Enter Room Dimensions
  │
  ▼
Send Request to Flask Backend
  │
  ▼
Room Placement & Validation
  │
  ├── Adjacency Checking
  ├── Connectivity Checking
  ├── Gap Validation
  └── Overlap Detection
  │
  ▼
Generate House Plan Options
  │
  ▼
Flutter 2D Visualization
  │
  ▼
View / Export Plan
```

---

## 🎥 Project Demo

Watch the Smart 2D House Plan Generator demonstration:

**[▶️ View Project Demo](https://drive.google.com/file/d/1aZ25b_yEEulMHtClPd3sEpp55icbSTDL/view?usp=drive_link)**

---

## 📚 Project Documentation

Full project documentation and related project resources:

**[📂 Open Project Documentation](https://drive.google.com/drive/folders/12PahXlfGJ9i7oBuin8vBVoewRm7oGW4L?usp=drive_link)**

---

## 🎯 Project Objectives

The main objectives of this project are to:

* Automate basic house floor-plan generation
* Reduce the effort required for manual layout planning
* Provide lifestyle-based room recommendations
* Generate practical room arrangements
* Validate room connectivity and spacing
* Provide an interactive 2D visualization
* Allow users to compare multiple generated plans
* Provide downloadable plan outputs

---

## 🔮 Future Improvements

Potential future enhancements include:

* 3D house plan visualization
* More advanced AI-based layout optimization
* Furniture placement
* User authentication
* Save and manage previous plans
* PDF export
* Improved architectural rules
* More detailed Vastu-based planning
* Cloud-based plan storage
* Mobile application support

---

## 👩‍💻 Developer

Developed as a **Smart 2D House Plan Generator** project using:

**Flutter Web • Dart • Python • Flask • Algorithms • 2D Visualization**




