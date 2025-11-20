import streamlit as st
import json
import os

# --- CONFIGURATION ---
FILE_GERMAN = 'input_data.json'
FILE_FRENCH_VERIFIED = 'translated_data_fr.json' 
FILE_PROPOSALS = 'proposed_translations_fr.json' 

st.set_page_config(layout="wide", page_title="Soumettre une Traduction")

# --- INJECTION DU CSS PERSONNALISÉ ---
# Ceci cible les champs de saisie (text_area et text_input) à l'intérieur du formulaire
# en se basant sur leur type et leur ordre d'apparition.
custom_css = """
<style>
/* QUESTION (Bleu - st.info) */
/* Cible le premier st.text_area dans le formulaire */
div[data-testid="stForm"] div[data-testid="stTextarea"]:nth-of-type(1) div[data-baseweb="textarea"] {
    border: 1px solid #007bff; 
    border-left: 5px solid #007bff;
    box-shadow: 0 0 5px rgba(0, 123, 255, 0.2);
}

/* CORRECT (Vert - st.success) */
/* Cible le premier st.text_input (qui est la réponse correcte) */
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(1) div[data-baseweb="input"] {
    border: 1px solid #28a745; 
    border-left: 5px solid #28a745;
    box-shadow: 0 0 5px rgba(40, 167, 69, 0.2);
}

/* INCORRECT 1 & 2 (Rouge - st.error) */
/* Cible les deux st.text_input suivants */
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(2) div[data-baseweb="input"],
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(3) div[data-baseweb="input"] {
    border: 1px solid #dc3545; 
    border-left: 5px solid #dc3545;
    box-shadow: 0 0 5px rgba(220, 53, 69, 0.2);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# CHARGEMENT DES DONNÉES
@st.cache_data
def load_data():
    try:
        with open(FILE_GERMAN, 'r', encoding='utf-8') as f:
            data_de = json.load(f)
    except FileNotFoundError:
        st.error(f"Fichier introuvable: {FILE_GERMAN}")
        return [], [], {}

    # Load verified French data (for display)
    if os.path.exists(FILE_FRENCH_VERIFIED):
        with open(FILE_FRENCH_VERIFIED, 'r', encoding='utf-8') as f:
            data_fr_verified = json.load(f)
    else:
        # Create empty French data based on German keys as a fallback
        data_fr_verified = [
            {"question": "Traduction manquante...", "correct": "", "incorrect_1": "", "incorrect_2": ""} 
            for _ in data_de
        ]
            
    # Load existing proposals
    if os.path.exists(FILE_PROPOSALS):
        with open(FILE_PROPOSALS, 'r', encoding='utf-8') as f:
            proposals = json.load(f)
    else:
        proposals = {}
            
    return data_de, data_fr_verified, proposals

data_de, data_fr_verified, proposals = load_data()

# GESTION DE L'ÉTAT (SESSION STATE)
if 'index' not in st.session_state:
    st.session_state.index = 0

idx = st.session_state.index

# --- SAUVEGARDE DE LA PROPOSITION ---
def save_proposal(index, q, c, i1, i2):
    """Sauvegarde la proposition dans le fichier dédié et passe au suivant."""
    proposals[str(index)] = {
        'question': q,
        'correct': c,
        'incorrect_1': i1,
        'incorrect_2': i2
    }
    
    # Save immediately
    with open(FILE_PROPOSALS, 'w', encoding='utf-8') as f:
        json.dump(proposals, f, indent=4, ensure_ascii=False)
    
    # Advance
    if idx < len(data_de) - 1:
        st.session_state.index += 1
        st.rerun()
    else:
        st.balloons()
        st.success("Félicitations ! Vous avez atteint la fin du fichier.")


# --- INTERFACE UTILISATEUR ---
if len(data_de) == 0:
    st.warning("Aucune donnée chargée.")
else:
    st.title(f"✍️ Soumettre une Traduction ({idx + 1}/{len(data_de)})")
    st.info("Vos propositions seront enregistrées pour vérification par l'administrateur.")
    
    # Barre de progression
    progress = (idx + 1) / len(data_de)
    st.progress(progress)

    col1, col2 = st.columns(2)

    # COLONNE GAUCHE : ALLEMAND (Référence)
    with col1:
        st.subheader("🇩🇪 Allemand (Original)")
        st.info(f"**Question:** {data_de[idx]['question']}")
        st.success(f"✅ {data_de[idx]['correct']}")
        st.error(f"❌ {data_de[idx]['incorrect_1']}")
        st.error(f"❌ {data_de[idx]['incorrect_2']}")
        
        # Affichage de la question vérifiée actuelle pour contexte (non éditable)
        st.divider()
        st.subheader("🇫🇷 Version VÉRIFIÉE Actuelle (Référence)")
        st.caption("La question actuellement validée est :")
        st.markdown(f"**{data_fr_verified[idx]['question']}**")


    # COLONNE DROITE : PROPOSITION (Éditable)
    with col2:
        st.subheader("📝 Votre Nouvelle Proposition")
        
        current_proposal = proposals.get(str(idx), {})
        
        # Déterminer les valeurs initiales : proposition existante ou version vérifiée
        initial_q = current_proposal.get('question', data_fr_verified[idx]['question'])
        initial_c = current_proposal.get('correct', data_fr_verified[idx]['correct'])
        initial_i1 = current_proposal.get('incorrect_1', data_fr_verified[idx]['incorrect_1'])
        initial_i2 = current_proposal.get('incorrect_2', data_fr_verified[idx]['incorrect_2'])

        
        with st.form(key='proposal_form'):
            
            # QUESTION (Visuel de st.info)
            st.markdown("##### ℹ️ Question (Texte à traduire)")
            # Champ de saisie simple pour un meilleur alignement
            new_q = st.text_area("Question", value=initial_q, height=100, label_visibility="collapsed")
            
            # CORRECT (Visuel de st.success)
            st.markdown("##### ✅ Réponse Correcte")
            # Champ de saisie simple pour un meilleur alignement
            new_c = st.text_input("Réponse Correcte", value=initial_c, label_visibility="collapsed")
            
            # INCORRECT 1 (Visuel de st.error)
            st.markdown("##### ❌ Incorrecte 1")
            # Champ de saisie simple pour un meilleur alignement
            new_i1 = st.text_input("Incorrecte 1", value=initial_i1, label_visibility="collapsed")
            
            # INCORRECT 2 (Visuel de st.error)
            st.markdown("##### ❌ Incorrecte 2")
            # Champ de saisie simple pour un meilleur alignement
            new_i2 = st.text_input("Incorrecte 2", value=initial_i2, label_visibility="collapsed")
            
            # --- NAVIGATION AND SUBMIT ---
            st.divider()
            c1, c2, c3 = st.columns([1, 1, 4])
            
            # Previous Button
            if c1.form_submit_button("⬅️ Préc."):
                 if idx > 0:
                    st.session_state.index -= 1
                    st.rerun()
            
            # Next Button
            if c2.form_submit_button("➡️ Suiv."):
                 # Check if we are at the end
                if idx < len(data_de) - 1:
                    st.session_state.index += 1
                    st.rerun()

            # Submit Button (Saves and moves to the next)
            submit = c3.form_submit_button("💾 Soumettre la Proposition & Avancer", type="primary")
            
            if submit:
                save_proposal(idx, new_q, new_c, new_i1, new_i2)
