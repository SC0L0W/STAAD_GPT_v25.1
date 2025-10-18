# 🏗️ STAAD GPT - AI Assistant for STAAD.Pro & Structural Engineering

<div align="center">

**Seamlessly Integrate AI and STAAD.Pro Commands**

*Intelligent Python-based GUI tool for structural engineers to interact with STAAD and AI models*

*Developed by* **[Your Name / Your Company]**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/yourprofile)

---

### 📊 Project Stats

![GitHub Views](https://komarev.com/ghpvc/?username=yourusername&label=Repository%20Views&color=0e75b6&style=flat)  
![GitHub Stars](https://img.shields.io/github/stars/yourusername/yourrepo?style=flat&color=yellow)  
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python)  
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

**Bridge AI and STAAD.Pro workflows effortlessly. Use natural language commands or precise STAAD instructions to streamline your structural analysis and modeling.**

</div>

---

## ✨ What Makes This Special

This Python GUI application combines AI-powered chat capabilities with STAAD.Pro automation. Built with `tkinter`, it offers an intuitive interface that recognizes user commands, parses common STAAD actions (nodes, beams, files), and communicates with STAAD to retrieve or modify models. Meanwhile, it leverages AI (via g4f and ChatGPT) to provide explanations, generate code snippets, or assist in modeling tasks—all in a single environment.

Whether you’re a structural engineer, analyst, or detailer, this tool simplifies complex workflows by integrating AI intelligence with STAAD commands, providing a responsive, customizable, and extensible platform.

---

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 🎨 **User-Friendly GUI**
- Custom images and icons for a modern look
- Scrollable text area for conversation history
- Style tags for message clarity
- Input box with Enter key support
- Responsive layout and image placement

### 📋 **STAAD Command Recognition & Execution**
- Parse commands: node coords, last node, beam length, create file
- Execute commands directly in STAAD via core controller
- Retrieve node/beam data and display in chat

</td>
<td width="50%">

### 🤖 **AI-Powered Assistance**
- Chat with ChatGPT or other g4f providers
- Context-aware conversations with history limit
- Prompts for ChatGPT login for enhanced responses
- Handle errors, timeouts, and provider issues gracefully

### 📝 **Outputs & Export**
- Generate detailed PDF reports (via reportlab)
- Export CAD drawings as DXF (via ezdxf, optional)
- Reinforcement & modeling documentation (future)

</td>
</tr>
</table>

---

## 📁 Application Architecture

```plaintext
your_project/
│
├── main.py                     # Main GUI & app logic
├── core/
│   └── staad_controller.py    # STAAD API interface & geometry
└── assets/
    └── frame0/
        ├── icon.ico            # App icon
        ├── image_1.png
        ├── image_2.png
        ├── image_3.png
        ├── image_4.png
        ├── image_5.png
        ├── button_1.png
        └── button_2.png
