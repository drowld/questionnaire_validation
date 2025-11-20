import streamlit as st
import json
import os

# --- CONFIGURATION ---
FILE_GERMAN = 'input_data.json'
FILE_FRENCH_VERIFIED = 'translated_data_fr.json' # The file that holds the final, verified data
FILE_PROPOSALS = 'proposed_translations_fr.json' # The file that holds unreviewed suggestions

st.set_page_config(layout="wide", page_title="Validateur de Propositions")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    try:
        with open(FILE_GERMAN, 'r', encoding='utf-8') as f:
            data_de = json.load(f)
        with open(FILE_FRENCH_VERIFIED, 'r', encoding='utf-8') as f:
            data_fr_verified = json.load(f)
        
        # Load proposals
        if os.path.exists(FILE_PROPOSALS):
            with open(FILE_PROPOSALS, 'r', encoding='utf-8') as f:
                proposals = json.load(f)
        else:
            proposals = {}
            
    except FileNotFoundError as e:
        st.error(f"Fichier essentiel introuvable: {e}. Assurez-vous que {FILE_GERMAN} et {FILE_FRENCH_VERIFIED} existent.")
        return [], [], {}

    # Get a list of indices that have pending proposals
    proposal_indices = sorted([int(k) for k in proposals.keys()])
    
    return data_de, data_fr_verified, proposals, proposal_indices

# --- LOGIQUE DE SAUVEGARDE ET DE GESTION DES PROPOSITIONS ---

def update_files(index_to_update, proposal_data, action):
    data_de, data_fr_verified, proposals, proposal_indices = load_data()
    
    # 1. Update Verified File (if accepted)
    if action == 'accept':
        st.toast(f"✅ Proposition ACCEPTÉE pour la question #{index_to_update + 1}!", icon="👍")
        # Update the main verified data structure
        data_fr_verified[index_to_update] = proposal_data
        
        # Write back the entire verified file
        with open(FILE_FRENCH_VERIFIED, 'w', encoding='utf-8') as f:
            json.dump(data_fr_verified, f, indent=4, ensure_ascii=False)
    
    elif action == 'reject':
        st.toast(f"❌ Proposition REJETÉE pour la question #{index_to_update + 1}.", icon="🗑️")

    # 2. Remove the proposal from the proposals file (for both accept/reject)
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
st.divider()

if not proposal_indices:
    st.success("🎉 Aucune proposition de traduction en attente de validation.")
else:
    # Get the index of the first pending proposal
    current_idx = proposal_indices[0]
    proposal = proposals[str(current_idx)]
    
    st.subheader(f"Proposition en attente : Question #{current_idx + 1} ({len(proposal_indices)} restantes)")
    
    col1, col2, col3 = st.columns(3)

    # COLUMN 1: GERMAN (REFERENCE)
    with col1:
        st.subheader("🇩🇪 Original (Allemand)")
        st.info(f"**Question:** {data_de[current_idx]['question']}")
        st.success(f"✅ {data_de[current_idx]['correct']}")
        st.error(f"❌ {data_de[current_idx]['incorrect_1']}")
        st.error(f"❌ {data_de[current_idx]['incorrect_2']}")

    # COLUMN 2: CURRENT VERIFIED FRENCH
    with col2:
        st.subheader("🇫🇷 Version VÉRIFIÉE Actuelle")
        st.text_area("Question VÉR.", value=data_fr_verified[current_idx]['question'], disabled=True, height=150)
        st.text_input("Correct VÉR.", value=data_fr_verified[current_idx]['correct'], disabled=True)
        st.text_input("Incorrect 1 VÉR.", value=data_fr_verified[current_idx]['incorrect_1'], disabled=True)
        st.text_input("Incorrect 2 VÉR.", value=data_fr_verified[current_idx]['incorrect_2'], disabled=True)
        
    # COLUMN 3: PROPOSED FRENCH
    with col3:
        st.subheader("📝 Proposition de la Communauté")
        st.text_area("Question PROP.", value=proposal['question'], disabled=True, height=150)
        st.text_input("Correct PROP.", value=proposal['correct'], disabled=True)
        st.text_input("Incorrect 1 PROP.", value=proposal['incorrect_1'], disabled=True)
        st.text_input("Incorrect 2 PROP.", value=proposal['incorrect_2'], disabled=True)
        
    st.divider()
    
    c_accept, c_reject = st.columns(2)
    
    if c_accept.button("✅ ACCEPTER la proposition (Confirmer la modification)", use_container_width=True, type="primary"):
        update_files(current_idx, proposal, 'accept')
        
    if c_reject.button("❌ REJETER la proposition (Garder l'ancienne)", use_container_width=True):
        update_files(current_idx, proposal, 'reject')