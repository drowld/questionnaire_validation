import streamlit as st
import json
import os

# --- CONFIGURATION ---
FILE_GERMAN = 'input_data.json'
FILE_FRENCH_VERIFIED = 'translated_data_fr.json' 
FILE_PROPOSALS = 'proposed_translations_fr.json' 

st.set_page_config(layout="wide", page_title="Soumettre une Traduction")

# --- INJECTION DU CSS PERSONNALISÉ ---
custom_css = """
<style>
/* Styles communs pour les champs de saisie */
div[data-testid="stForm"] div[data-testid="stTextarea"] div[data-baseweb="textarea"] > textarea,
div[data-testid="stForm"] div[data-testid="stTextInput"] div[data-baseweb="input"] > input {
    padding: 10px; 
    border: none !important; 
}

/* TARGET PROPOSAL FORM ONLY - All fields keep their color */
/* Question - Bleu */
div[data-testid="stForm"] div[data-testid="stTextarea"]:nth-of-type(1) div[data-baseweb="textarea"] {
    background-color: #e6f0ff;
    border: 1px solid #007bff;
}

/* Correct Answer - Vert */
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(1) div[data-baseweb="input"] {
    background-color: #f0fff0;
    border: 1px solid #28a745;
}

/* Incorrect 1 - Rouge */
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(2) div[data-baseweb="input"] {
    background-color: #fff0f0;
    border: 1px solid #dc3545;
}

/* Incorrect 2 - Rouge */
div[data-testid="stForm"] div[data-testid="stTextInput"]:nth-of-type(3) div[data-baseweb="input"] {
    background-color: #fff0f0;
    border: 1px solid #dc3545;
}

/* Disable interaction styling for readonly fields */
div[data-testid="stForm"] textarea:disabled,
div[data-testid="stForm"] input:disabled {
    background-color: inherit !important;
    cursor: not-allowed;
    opacity: 0.9;
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

    # COLONNE GAUCHE : ALLEMAND (Référence - Readonly fields)
    with col1:
        st.subheader("🇩🇪 Allemand (Original)")
        
        st.text_area("Question (DE)", 
                    value=data_de[idx]['question'], 
                    height=100, 
                    label_visibility="collapsed",
                    disabled=True)
        
        st.text_input("Réponse Correcte (DE)", 
                     value=data_de[idx]['correct'], 
                     label_visibility="collapsed",
                     disabled=True)
        
        st.text_input("Incorrecte 1 (DE)", 
                     value=data_de[idx]['incorrect_1'], 
                     label_visibility="collapsed",
                     disabled=True)
        
        st.text_input("Incorrecte 2 (DE)", 
                     value=data_de[idx]['incorrect_2'], 
                     label_visibility="collapsed",
                     disabled=True)
        
        # Affichage de la question vérifiée actuelle pour contexte
        st.divider()
        st.subheader("🇫🇷 Version VÉRIFIÉE Actuelle (Référence)")
        st.caption("La question actuellement validée est :")
        st.markdown(f"**{data_fr_verified[idx]['question']}**")


    # COLONNE DROITE : PROPOSITION (Editable)
    with col2:
        st.subheader("📝 Votre Nouvelle Proposition")
        
        current_proposal = proposals.get(str(idx), {})
        
        # Déterminer les valeurs initiales : proposition existante ou version vérifiée
        initial_q = current_proposal.get('question', data_fr_verified[idx]['question'])
        initial_c = current_proposal.get('correct', data_fr_verified[idx]['correct'])
        initial_i1 = current_proposal.get('incorrect_1', data_fr_verified[idx]['incorrect_1'])
        initial_i2 = current_proposal.get('incorrect_2', data_fr_verified[idx]['incorrect_2'])

        
        with st.form(key='proposal_form'):
            
            # QUESTION - Bordure BLEUE
            new_q = st.text_area("Question", 
                                value=initial_q, 
                                height=100, 
                                label_visibility="collapsed", 
                                placeholder="ℹ️ Entrez la question traduite ici (Bleu pour la question)...")
            
            # CORRECT - Bordure VERTE
            new_c = st.text_input("Réponse Correcte", 
                                 value=initial_c, 
                                 label_visibility="collapsed",
                                 placeholder="✅ Entrez la réponse correcte traduite ici (Vert pour le correct)...")
            
            # INCORRECT 1 - Bordure ROUGE
            new_i1 = st.text_input("Incorrecte 1", 
                                  value=initial_i1, 
                                  label_visibility="collapsed",
                                  placeholder="❌ Entrez la première mauvaise réponse traduite ici (Rouge pour l'incorrect)...")
            
            # INCORRECT 2 - Bordure ROUGE
            new_i2 = st.text_input("Incorrecte 2", 
                                  value=initial_i2, 
                                  label_visibility="collapsed",
                                  placeholder="❌ Entrez la deuxième mauvaise réponse traduite ici (Rouge pour l'incorrect)...")
            
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
