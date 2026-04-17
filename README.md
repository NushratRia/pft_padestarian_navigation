# PFT Navigator — Patrick F. Taylor Hall Indoor Navigation

A full-stack web application for navigating LSU's Patrick F. Taylor Hall.
Built with **Flask** (backend) + **Vanilla HTML/CSS/JS** (frontend).

---

## Features

- **Search** by room number, lab name, or department
- **Interactive floor plan** with pan & zoom (mouse, touch, scroll wheel)
- **Route planner** — select Start & End rooms, draws a highlighted path on the map
- **Step-by-step directions** with turn-by-turn instructions
- **Multi-floor navigation** — automatically routes through the central elevators
- **Room info popups** — click any pin for details, set as start/end, or bookmark
- **Session history** — recent routes saved per browser session
- **Saved/pinned locations** — bookmark favourite rooms

---

## Project Structure

```
pft_nav/
├── app.py                  # Flask backend — routes, room DB, navigation logic
├── requirements.txt
├── templates/
│   └── index.html          # Main page (Jinja2)
└── static/
    ├── css/
    │   └── style.css       # All styling (LSU purple/gold dark theme)
    ├── js/
    │   └── app.js          # All frontend logic
    └── images/
        ├── floor1.png      # Floor 1 plan
        ├── floor2.png      # Floor 2 plan
        └── floor3.png      # Floor 3 plan
```

---

## Setup & Run

### 1. Install Python dependencies
```bash
cd pft_nav
pip install -r requirements.txt
```

### 2. Run the development server
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## How to Use

| Action | How |
|---|---|
| Search a room | Type in the search bar (room number, name, or department) |
| Set start point | Click a search result → "Set as Start" in popup, or click "Set as Start" directly |
| Set destination | Same as above but "Set as Destination" |
| Get directions | Click the gold **Get Directions** button |
| View steps | Steps tab in the left panel updates with turn-by-turn instructions |
| Pan the map | Click and drag |
| Zoom | Scroll wheel or +/− buttons |
| Switch floors | Use Floor 1 / Floor 2 / Floor 3 buttons at the top |
| Save a location | Click any pin → bookmark icon in popup |
| View history | "History" tab in the left panel |

---

## Room Database

The app includes **80+ rooms** across all 3 floors, organized by department:

| Color | Department |
|---|---|
| 🟡 Yellow | Chemical Engineering |
| 🟣 Lavender | Mechanical/Industrial Engineering |
| 🔴 Red | Civil/Environmental Engineering |
| 🔵 Blue | Petroleum Engineering |
| 🟢 Light Green | Electrical/Computer Engineering |
| 🟠 Orange | Computer Science |
| 🌲 Dark Green | Construction Management |
| 🩵 Light Blue | College (shared spaces) |

---

## Extending the App

To add more rooms, edit the `ROOMS` dictionary in `app.py`:

```python
"ROOM_NUMBER": {
    "name": "Room Display Name",
    "floor": 1,           # 1, 2, or 3
    "dept": "Chemical Engineering",
    "type": "lab",        # lab | classroom | office | amenity | auditorium
    "x": 0.55,            # fraction of image width [0.0 – 1.0]
    "y": 0.42,            # fraction of image height [0.0 – 1.0]
    "keywords": ["search", "terms", "here"]
},
```

The `x` and `y` coordinates are fractions of the floor plan image dimensions,
so `x=0.5, y=0.5` is the center of the image.

---

## Tech Stack

- **Backend**: Python / Flask
- **Frontend**: Vanilla JS (ES2020), HTML5, CSS3
- **Map overlay**: SVG with animated path drawing
- **Session storage**: Flask server-side sessions (cookie-based)
- **Fonts**: Syne (display) + DM Sans (body) via Google Fonts
- **No external JS libraries required**

---

## Team

Built for HCI / CSC 4370 — Milestone 3
LSU College of Engineering — Patrick F. Taylor Hall Navigation System
