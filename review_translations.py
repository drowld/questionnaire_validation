import streamlit as st
import json
import os

# --- CONFIGURATION ---
FILE_GERMAN = 'input_data.json'
FILE_FRENCH_VERIFIED = 'translated_data_fr.json' # The file that holds the final, verified data
FILE_PROPOSALS = 'proposed_translations_fr.json' # The file that holds unreviewed suggestions

st.set_page_config(layout="wide", page_title="Validateur de Propositions (ADMIN)")

# --- CHARGEMENT DES DONNÉES ---
# Clear the cache every time this function is called to ensure we load the latest files
@st.cache_data(ttl=1)
def load_data():
    try:
        with open(FILE_GERMAN, 'r', encoding='utf-8') as f:
            data_de = json.load(f)
        
        # Initialize or load verified French data
        if os.path.exists(FILE_FRENCH_VERIFIED):
            with open(FILE_FRENCH_VERIFIED, 'r', encoding='utf-8') as f:
                data_fr_verified = json.load(f)
        else:
            data_fr_verified = data_de.copy() # Use German as a placeholder if file is missing

        # Load proposals
        if os.path.exists(FILE_PROPOSALS):
            with open(FILE_PROPOSALS, 'r', encoding='utf-8') as f:
                proposals = json.load(f)
        else:
            proposals = {}
            
    except FileNotFoundError as e:
        st.error(f"Fichier essentiel introuvable: {e}. Assurez-vous que {FILE_GERMAN} et {FILE_FRENCH_VERIFIED} existent.")
        return [], [], {}, []

    # Get a list of indices that have pending proposals
    proposal_indices = sorted([int(k) for k in proposals.keys()])
    
    return data_de, data_fr_verified, proposals, proposal_indices

# --- LOGIQUE DE SAUVEGARDE ET DE GESTION DES PROPOSITIONS ---

def update_files(index_to_update, proposal_data, action):
    # Retrieve current data (will use the cached version from load_data)
    data_de, data_fr_verified, proposals, proposal_indices = load_data()
    
    # 1. Update Verified File (if accepted/committed)
    if action == 'commit':
        st.toast(f"✅ Version Éditée COMMITTÉE pour la question #{index_to_update + 1}!", icon="👍")
        # Update the main verified data structure with the proposal data
        data_fr_verified[index_to_update] = proposal_data
        
        # Write back the entire verified file
        with open(FILE_FRENCH_VERIFIED, 'w', encoding='utf-8') as f:
            json.dump(data_fr_verified, f, indent=4, ensure_ascii=False)
    
    elif action == 'reject':
        st.toast(f"❌ Proposition REJETÉE pour la question #{index_to_update + 1} (Version actuelle conservée).", icon="🗑️")

    # 2. Remove the proposal (for both commit/reject)
    if str(index_to_update) in proposals:
        del proposals[str(index_to_update)]
        
        # Write back the entire proposals file
        with open(FILE_PROPOSALS, 'w', encoding='utf-8') as f:
            json.dump(proposals, f, indent=4, ensure_ascii=False)
    
    # Rerun to clear the cache and load the next pending item
    st.cache_data.clear()
    st.rerun()


# --- INTERFACE UTILISATEUR ---

data_de, data_fr_verified, proposals, proposal_indices = load_data()

st.title("🛡️ Outil de Validation (Admin)")
st.caption("Examinez et validez les propositions de traduction de la communauté.")
st.divider()


if not proposal_indices:
    st.success("🎉 Aucune proposition de traduction en attente de validation. Tout est à jour !")
else:
    # Get the index of the first pending proposal
    current_idx = proposal_indices[0]
    proposal = proposals[str(current_idx)]
    
    st.subheader(f"Proposition en attente : Question #{current_idx + 1} / {len(data_de)} (Reste : {len(proposal_indices)})")
    
    col1, col2, col3 = st.columns(3)

    # --- COLUMN 1: GERMAN (REFERENCE) ---
    with col1:
        st.subheader("🇩🇪 Original (Allemand)")
        st.info(f"**Question:** {data_de[current_idx]['question']}")
        st.success(f"✅ {data_de[current_idx]['correct']}")
        st.error(f"❌ {data_de[current_idx]['incorrect_1']}")
        st.error(f"❌ {data_de[current_idx]['incorrect_2']}")

    # --- COLUMN 2: CURRENT VERIFIED FRENCH ---
    with col2:
        st.subheader("🇫🇷 Version VÉRIFIÉE Actuelle")
        st.caption("Ceci est la version LIVE actuellement utilisée.")
        st.text_area("Question VÉR.", value=data_fr_verified[current_idx]['question'], disabled=True, height=150, help="Version actuelle (Non modifiable ici)")
        st.text_input("Correct VÉR.", value=data_fr_verified[current_idx]['correct'], disabled=True)
        st.text_input("Incorrect 1 VÉR.", value=data_fr_verified[current_idx]['incorrect_1'], disabled=True)
        st.text_input("Incorrect 2 VÉR.", value=data_fr_verified[current_idx]['incorrect_2'], disabled=True)
        
    # --- COLUMN 3: PROPOSED FRENCH (EDITABLE DRAFT) ---
    with col3:
        st.subheader("📝 Votre Brouillon ÉDITABLE")
        st.caption("Basé sur la proposition de la communauté. Modifiez si nécessaire.")
        
        # Use a form to capture edits before commit
        with st.form(key="review_form", clear_on_submit=True):
            # Pre-fill with the community's proposal
            draft_q = st.text_area("Question", value=proposal['question'], height=150)
            draft_c = st.text_input("Réponse Correcte", value=proposal['correct'])
            draft_i1 = st.text_input("Incorrecte 1", value=proposal['incorrect_1'])
            draft_i2 = st.text_input("Incorrecte 2", value=proposal['incorrect_2'])

            # Action Buttons inside the form
            c_commit, c_reject = st.columns(2)
            
            commit_button = c_commit.form_submit_button("✅ COMMETTRE (Sauvegarder et Valider)", type="primary", use_container_width=True)
            
            reject_button = c_reject.form_submit_button("❌ REJETER la proposition", use_container_width=True)


    st.divider()
    
    # Handle button actions outside the form (to use Rerun)
    if commit_button:
        # Use the finalized data from the draft inputs
        final_data = {
            'question': draft_q, 
            'correct': draft_c, 
            'incorrect_1': draft_i1, 
            'incorrect_2': draft_i2
        }
        update_files(current_idx, final_data, 'commit')
        
    if reject_button:
        # The proposal data is irrelevant, but we still need to pass it to the function
        update_files(current_idx, proposal, 'reject')
