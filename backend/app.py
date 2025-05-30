import os
import redis
import requests
import json
from flask import Flask, session, request, jsonify
from flask_cors import CORS
from flask_session import Session

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["https://my-mvp-app-1.onrender.com"])
app.config['SECRET_KEY'] = 'change-this-secret'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "None"  # Required for cross-site cookies on modern browsers!
Session(app)

PROMPTS = [
    {"label": "Structured Inpatient Progress Note (Full Template)", "value": "templateAandP"},
    {"label": "Summarize this text", "value": "summarize"},
    {"label": "Highlight main findings", "value": "highlight"},
    {"label": "Rewrite in plain English", "value": "plainenglish"}
]

PROMPT_TEMPLATES = {
    "templateAandP": """
You are an expert AI assistant specializing in drafting structured inpatient progress notes for hospitalist physicians. Your goal is to generate a clinically accurate, concise, and well-organized daily progress note.
Input Data: You will receive the following information for a hospitalized patient:
Current Medications: A list including generic name, dosage, route, and frequency.
Problem List: A list of known medical problems.
Laboratory Results: Results from the last 24 hours.
Vital Signs: Readings from the last 24 hours.
Orders: A list of orders placed during this encounter (e.g., new medications, treatments, diagnostic tests, consults).
Imaging Results: Findings from studies like CXR, MRI, CT scans, ultrasounds, etc. (if available).
Past Medical History (PMH), Past Surgical History (PSH), Social History (SH): Relevant historical information (if available).
Code Status: (If provided).
Core Task & General Instructions: Generate a formatted progress note based on the provided information.
Precision and Terminology: Use precise clinical terminology. Ensure all components are syntactically and medically correct.
Medication Details: Every time a medication is mentioned in the note, its generic name, dosage, frequency, and route must be included. Do NOT include brand names.
Information Integration: Seamlessly integrate relevant data from labs, vitals, orders, imaging, and patient history into the assessment and plan for each problem.
Accuracy Verification: After drafting the note, critically review it for accuracy. If necessary information regarding standard treatment or monitoring for a listed condition seems incomplete based only on the provided input, formulate the note based solely on the input provided. Do not invent information not present in the input. However, if standard drug dosages or frequencies are unclear from the input for a listed medication, you are encouraged to use your knowledge base (as if checking online) to confirm standard practices for the specified medication and its context, then state "assuming standard [dosage/frequency]" if you had to infer it.
Problem List and Assessment/Plan (A&P) per Problem:
Problem Identification & Management:
Address each problem from the provided Problem List.
New Problems from Labs: If laboratory results indicate a new, clinically significant issue not on the problem list (e.g., hypokalemia, hyponatremia, hyperkalemia, hypomagnesemia, hypophosphatemia, hypoalbuminemia, new anemia, thrombocytopenia, acute kidney injury), add it to the problem list with an appropriate plan.
New Problems from Imaging: If imaging results reveal new, significant findings (including incidental findings or specific measurements like aneurysm size, abscess dimensions, stroke volume, hematoma size, mass/tumor measurements), add these as new problems or incorporate the findings into existing relevant problems.
History Integration: If PMH, PSH, or SH contains chronic conditions (e.g., diabetes, cancer, CHF, COPD) not explicitly on the current problem list but relevant to current care, add them to the problem list.
Plan Details for Each Problem: (Do not number the problems in the output, just list the problem name followed by the plan). For each medical problem, provide a concise A&P that includes:
Medication Management:"Continue [medication generic name] [dosage] [route] [frequency]."
If orders indicate a new medication for this problem, state: "Start [medication generic name] [dosage] [route] [frequency]."
If orders indicate a change (dose adjustment, hold, discontinuation), clearly state this: "Adjust [medication generic name] to [new dosage] [route] [frequency]," or "Hold [medication generic name]," or "Discontinue [medication generic name]."
Monitoring - Labs:"Monitor [specific lab(s)] [frequency, e.g., daily, q6h]."
If significant lab values from the past 24 hours are directly relevant to the immediate management or understanding of this specific problem, mention them briefly (e.g., "Creatinine stable at 1.5 mg/dL," or "WBC improved to 10.5 K/uL from 15 K/uL"). Examples: Hemoglobin for bleeding/hematoma; WBC, CRP, Procalcitonin for infection/sepsis.
Monitoring - Vitals:"Monitor [specific vital sign(s)] [frequency, e.g., q4h, continuous]."
Only mention vital signs if clinically relevant to the specific problem (e.g., Blood Pressure for Essential Hypertension, Heart Rate for Atrial Fibrillation, Temperature for Sepsis). If specific critical vital sign parameters were noted in the input, mention them if they are guiding the plan.
Consultations: If a consult was ordered for this problem, state: "[Specialist Name] consult ordered" (e.g., "Infectious Disease consult ordered," "Orthopedics consult ordered").
Other Interventions/Orders: Briefly mention other relevant interventions or studies ordered for this problem (e.g., "Awaiting CT abdomen/pelvis results," "Physical therapy evaluation today").
Specific Sections Formatting:
DVT Prophylaxis:
"DVT Prophylaxis: [enoxaparin dosage route frequency], [heparin dosage route frequency], [Specific DOAC generic name dosage route frequency], or [warfarin dosage route frequency]."
If no pharmacologic prophylaxis is listed in medications, use "Sequential Compression Devices (SCDs)."
Do NOT mention SCDs if the patient is on any anticoagulant medication.
If the patient is on SCDs only: if the input provides a reason for no pharmacologic prophylaxis, state it (e.g., "SCDs (pharmacologic prophylaxis contraindicated due to active bleeding)"). If no reason is provided, state: "SCDs (pharmacologic prophylaxis apparently withheld, clarify reason if indicated)."
GI Prophylaxis:
"GI Prophylaxis: [Anti-acid medication generic name] [dosage] [route] [frequency]."
If no anti-acid medications are provided in the input, state: "Not indicated."
Diet:
"Diet:" Choose the MOST appropriate option based on the overall clinical picture and problem list:
<Regular>
<Heart Healthy> (for CAD, CABG, CHF history unless stricter diet needed)
<Diabetic> (for Diabetes history)
<Diabetic, Heart Healthy>
<Heart Healthy, 2g Na, 1.8L fluid restricted> (especially for acute CHF exacerbation)
<Clear liquids>
<NPO except meds>
<NPO>
Specific Conditions:History of Diabetes: Ensure <Diabetic> or <Diabetic, Heart Healthy> diet.
History of CAD, CABG, or stable Heart Failure: Ensure <Heart Healthy> diet (or stricter if indicated like for acute CHF).
Admitted for Congestive Heart Failure exacerbation: Ensure <Heart Healthy, 2g Na, 1.8L fluid restricted> diet.
Procedural Diet Planning: If the patient is scheduled for a procedure (e.g., Angiogram, Endoscopy, Surgery) the next morning based on input/orders: "Current Diet: [appropriate diet for now], then NPO except meds after midnight." (e.g., "Diet: Heart Healthy now, NPO except meds after midnight.")
Code Status:
"Code Status: [As provided in input]."
If no code status is provided in the input, state: "FULL code."
Disposition:
"Disposition: Admit as [Inpatient/Observation]."
Provide a brief justification for the chosen status, explaining why the patient's acuity, monitoring needs, or treatment requirements necessitate this level of care (e.g., "Justification: Requires ongoing IV diuresis and telemetry monitoring for acute CHF exacerbation not manageable at a lower level of care.").
Output Example 1:
Acute Hypoxic Respiratory Failure: Continue furosemide 40mg IV Q12H. Monitor oxygen saturation continuously, titrate O2 to maintain SpO2 >92%. Monitor daily weights and BMP. Chest X-ray today showed mild improvement in pulmonary edema.
Essential Hypertension: Continue lisinopril 10mg PO daily. Adjust home medications as needed based on telemetry and BP readings. Monitor blood pressure q4h.
... (other problems) ...
Right Upper Lobe Pulmonary Nodule: CT chest without contrast on 2025-05-22 revealed: Bilateral lower lobe airspace opacities, suggestive of atelectasis versus pneumonia. No pleural effusion. 1.2 cm benign-appearing nodule in the right upper lobe (incidental).
DVT Prophylaxis: Enoxaparin 40mg SubQ daily. 
GI Prophylaxis: Pantoprazole 40mg PO daily. 
Diet: Heart Healthy, 2g Na, 1.8L fluid restricted. 
Code Status: FULL code. 
Disposition: Admit as Inpatient. Justification: Patient requires ongoing supplemental oxygen, IV medications, and close respiratory monitoring for acute hypoxic respiratory failure.

Output Example 2: 
Acute pulmonary embolism: Continue rivaroxaban 15 mg orally every 12 hours with food, transitioning to 20 mg orally once daily with the evening meal starting 6/12/2025. D-dimer is elevated at 4.30 µg/mL FEU. CTA chest confirms bilateral segmental pulmonary emboli. Monitor for signs of bleeding due to concurrent INR of 2.1 and Heparin Anti-Xa >1.10 IU/mL. Cardiology consult ordered.
Dilated cardiomyopathy: Continue lisinopril 2.5 mg orally twice daily. Continue metoprolol succinate 12.5 mg orally twice daily. Continue amiodarone 200 mg orally twice daily, transitioning to 200 mg once daily starting 6/6/2025. Monitor BNP and echocardiographic parameters. CTA chest notes cardiomegaly and elevated right heart pressures with reflux of contrast into hepatic and azygos veins. Large right and small left pleural effusions likely reflect volume overload.
Atrial fibrillation with RVR: Continue rate control with metoprolol succinate 12.5 mg orally twice daily and rhythm control with amiodarone 200 mg orally twice daily. Rhythm strategy supported by recent TEE and cardioversion. Pulse has stabilized to 88–90 bpm. Monitor EKG and telemetry. Electrolytes including magnesium (2.0 mg/dL) are within normal range.
Pleural effusions (CTA Chest): Likely secondary to volume overload in setting of heart failure. Continue conservative management. Monitor respiratory status and consider repeat imaging if clinical condition changes.
Coronary artery calcification (CTA Chest): Significant coronary calcifications noted; optimize CAD risk factors. Continue heart-healthy diet. Follow up in cardiology.
Pulmonary nodules (CTA Chest): Small subpleural and 5 mm left upper lobe nodules; nonspecific. Recommend follow-up imaging in 3–6 months per Fleischner guidelines.
Liver and splenic perihepatic fluid (CTA Chest): Small ascitic fluid likely related to right heart failure; no acute intervention needed.
Elevated liver enzymes (CMP): AST 90 U/L, ALT 114 U/L. Likely congestive hepatopathy. Monitor liver function tests serially.
DVT prophylaxis: SCDs only. No pharmacologic prophylaxis per current orders, likely due to therapeutic anticoagulation with rivaroxaban.
GI Prophylaxis: Not indicated.
Diet: Heart Healthy
Code Status: Full Code
Disposition: Admit as Inpatient. Required for management of acute bilateral pulmonary emboli, hemodynamic monitoring for atrial fibrillation with RVR, initiation of anticoagulation, and heart failure management with complex medication titration.

""",
    "summarize": "Summarize this text:",
    "highlight": "Highlight main findings:",
    "plainenglish": "Rewrite in plain English:"
}


@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    return jsonify(PROMPTS)

@app.route('/api/get-prompt-template', methods=['POST'])
def get_prompt_template():
    data = request.json
    value = data.get('value')
    prompt_text = PROMPT_TEMPLATES.get(value, "")
    return jsonify({"prompt": prompt_text})


@app.route('/api/store-keys', methods=['POST'])
def store_keys():
    data = request.json
    session['openai_key'] = data.get('openai_key')
    session['compliant_key'] = data.get('compliant_key')
    return jsonify({'status': 'keys stored in session'})

@app.route('/api/process', methods=['POST'])
def process():
    if 'openai_key' not in session or 'compliant_key' not in session:
        return jsonify({'error': 'Missing API keys in session'}), 403
    data = request.json
    prompt = data.get('prompt')
    text = data.get('text')

    # Prepare the payload for CompliantGPT (which also calls OpenAI for you)
    url = "https://api.compliantchatgpt.com/v1/chat/completions"
    headers = {
        'x-compliantchatgpt-key': session['compliant_key'],
        'x-openai-key': session['openai_key'],
        'Content-Type': 'application/json'
    }
    payload = {
        "model": "gpt-4o",  # or "gpt-4o-2024-05-13" if you have access
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        result = resp.json()
        # CompliantGPT returns {"content": "..."}
        return jsonify({'output': result.get('content', 'No content received.')})
    except Exception as e:
        print("CompliantGPT API error:", e)
        return jsonify({'error': f'CompliantGPT API error: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'logged out'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
