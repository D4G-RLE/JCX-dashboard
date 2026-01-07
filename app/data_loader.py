# app/data_loader.py

# Fonction pour charger les données projets depuis un fichier
def load_projects_data(real=True):
    """
    real=True  => charge tes vraies données
    real=False => charge les données exemples (pour GitHub)
    """
    if real:
        from app.projects_data import projects_data
    else:
        from app.projects_data_example import projects_data
    return projects_data
