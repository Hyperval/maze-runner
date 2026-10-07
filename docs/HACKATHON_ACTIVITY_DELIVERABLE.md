# Hackathon Preparation Activity — Final Submission Deliverable

**Course / Track:** B25CS0311 Portfolio Building / Hackathon Preparation  
**Institution:** REVA University — School of Computer Science and Engineering  
**Date of Submission:** 07/10/2026  

---

## 1. Team Roster

| Member Name | Program & Section | Primary Role | Key Skill / Strength |
| :--- | :--- | :--- | :--- |
| **Akshay N** | B.Tech CSE (3B) | Frontend Developer | Game loop execution, user input handling, viewport rendering, and HUD state management (`pygame-ce`) |
| **Abdullah Subhaan K** | B.Tech CSE (3B) | UI / Level Design | Maze generation aesthetics, translucent search overlay visualization, sprite styling, and level design |
| **Akhil Sathish Kumar** | B.Tech CSE (3B) | Backend, Bridging & Testing | Pathfinding algorithms (BFS, A*), game integration bridging, and automated test suite design (`test_pathfinding.py`) |
| **Christen Mendes** | B.Tech CSE (3B) | Presentation, Benchmarking & Docs | Slide deck preparation (`python-pptx`), benchmark analysis (`benchmark.py`), demo narration, and technical documentation |

---

## 2. Selected Hackathon Details

| Parameter | Details |
| :--- | :--- |
| **Hackathon Name** | **Syntax Error 2026** *(Student Innovation Track)* / **REVA CSE Portfolio Hackathon** |
| **Platform** | Devfolio / Unstop / University Portal |
| **Registration / Portal Link** | [https://devfolio.co/hackathons](https://devfolio.co/hackathons) *(Repository: [https://github.com/Hyperval/maze-runner](https://github.com/Hyperval/maze-runner))* |
| **Mode** | Hybrid / Online |
| **Team-Size Limit** | 2 – 4 Members (Our team: 4 members) |
| **Eligibility** | Open to undergraduate Computer Science / Engineering students |
| **Submission Requirements** | Working code repository, automated test suite, runnable demonstration, slide deck presentation, and viva evaluation |

---

## 3. Problem Statement Ideas & Evaluation Matrix

| Idea | Problem | Target Users | Feasibility | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Idea 1 (Selected): Problem Statement #15 — Maze Runner with AI-Controlled Enemy** | Conventional pathfinding demonstrations treat algorithms as hidden black boxes, making it difficult to visualize how different search algorithms traverse state spaces under real-time constraints. | CS students, algorithm learners, game developers | **High** *(Self-contained in Python, zero external APIs/hardware dependencies, reliably verifiable)* | **High** *(Side-by-side BFS vs A* visual search expansion, 233 passing unit tests, and empirical benchmarking)* |
| **Idea 2: Campus Facility & Maintenance Grievance Tracker** | Hostel residents encounter delays in routine repairs due to paper registers with no tracking or SLA escalation. | Hostel residents, wardens, maintenance staff | **Medium** *(Requires full web database stack, auth, and external hosting)* | **Medium** |
| **Idea 3: Peer-to-Peer Academic Resource & Lab Gear Exchange** | University course notes and specialized lab microcontrollers are fragmented across informal WhatsApp groups. | Undergraduate students, lab faculty | **Low** *(Requires inventory handling, deposit trust logic, and moderation)* | **Medium** |

**Selection Rationale:**  
We selected **Idea 1 (Maze Runner with AI-Controlled Enemy)** because it solves an authentic algorithmic problem with high feasibility in the allocated time frame. It enables a robust, self-contained implementation with rigorous automated testing and visual demonstration of AI decision-making.

---

## 4. Problem Statement & Planned Technology Stack

### One-Paragraph Scoped Problem Statement
Traditional pathfinding games hide AI decision-making under the hood, preventing students and evaluators from observing how different search algorithms explore state spaces under identical constraints. Computer science students and algorithm enthusiasts often struggle to intuitively grasp the trade-offs between uninformed searches like Breadth-First Search (BFS) and informed heuristic searches like A* when reading static textbooks. We are building **Maze Runner with AI-Controlled Enemy**, a 2D grid navigation game where the player navigates a dynamically generated, braided maze while an AI enemy actively pursues them. The application computes optimal routes at every tick, draws expanded search cells in real time as a translucent overlay to make the AI's reasoning visible, and introduces dual-algorithm comparison and predictive interception across progressive difficulty tiers.

### Planned Technology Stack
- **Frontend / Graphics:** Python 3.10+ with `pygame-ce 2.5.8` (game loop, viewport rendering, sprite logic, and translucent overlay rendering).
- **Backend / Core Engine:** Python standard library algorithms — Breadth-First Search (BFS via `collections.deque`), A* Search (Manhattan distance heuristic via `heapq`), Recursive Backtracker maze generation with cycle braiding.
- **Data Structures / Storage:** Pure in-memory grid graphs, priority queues, coordinate sets, and local persistent JSON storage for best completion times.
- **Testing & Verification:** Custom headless automated test suite (`test_pathfinding.py` — 233 automated test checks) and bot simulation harness (`autoplay.py` with 500 playthroughs).
- **Benchmarking & Visualization:** `matplotlib 3.10` (`benchmark.py` measuring expanded cell counts over 50 generated mazes).
- **Tooling & Presentation:** `python-pptx` (programmatic 16:9 slide generation), `tools_record_demo.py` (backup demo capture), Git and GitHub.

---

## 5. Team Collaboration & Shared Document

- **Repository Link:** [https://github.com/Hyperval/maze-runner](https://github.com/Hyperval/maze-runner)  
- **Team Documentation / Issue Link:** [https://github.com/Hyperval/maze-runner/blob/master/docs/HACKATHON_ACTIVITY_DELIVERABLE.md](https://github.com/Hyperval/maze-runner/blob/master/docs/HACKATHON_ACTIVITY_DELIVERABLE.md)  
- **Access Confirmation:** Verified. The repository and documents are accessible to all 4 team members with active collaborator rights.

---

## 6. Deliverable / Evidence Checklist (LMS Ready)

- [x] **Team roster** listing each member's name and primary role.
- [x] **Direct link** to the selected hackathon on Devfolio / Unstop / GitHub.
- [x] **One-paragraph problem statement** describing the problem, target users, and proposed solution.
- [x] **Technology stack** listed below the problem statement.
- [x] **Shared Google Doc or GitHub Issue link** provided.
- [x] **Confirmation** that the document/issue is accessible to all team members.
