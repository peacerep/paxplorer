# PA-Xplorer

**PA-Xplorer** is an interactive Shiny for Python web application that allows researchers and practitioners to explore the **PA-X Peace Agreements Database**.  
The app provides visual and downloadable summaries of peace agreements, processes, topics, and actors — enabling easy discovery, analysis, and export of trends in global peace data.

---

## Features

- **Overview Dashboard:** Explore high-level global trends in peace agreements.  
- **Peace Process Analysis:** Examine agreements by process, stage, and time.  
- **Topic Explorer:** Visualize issues addressed across agreements and their evolution.  
- **Actors Dashboard:** Analyze signatories, actor types, and their involvement patterns.  
- **Dynamic Exports:**  Export plots to PNG with branded footer and logo.  
- **Interactive Controls:** Filter by date range, stage, actor type, or topic category.  

## Local set up
1. Clone repo
2. Install dependencies
pip install -r requirements.txt
3. Run app locally
shiny run app.py --reload

## Deployment - log in credentials and then run:
rsconnect deploy shiny "." --name peacerep --title paxplorer

### Libraries in use
Shiny for Python
pandas
matplotlib
plotly
python-docx (Word export)
upsetplot (topic intersection charts)

## Contributors
Developed for the PA-X Team - PeaceRep at the University of Edinburgh Law School by Niamh Henry.
For any questions, concerns, contributions - reach out to nhenry2@ed.ac.uk

## License
This project is for research and educational use. Contact the maintainers for reuse or redistribution permissions.
© 2025 PA-X Research Team.
Terms of use: please leave citation and branding in exported png plots.