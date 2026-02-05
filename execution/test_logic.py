
# Reproduction of logic from sync_meta_metrics.py

STRICT_OBJECTIVES = [
    'OUTCOME_LEADS', 
    'OUTCOME_SALES',
    'LEAD_GENERATION',
    'CONVERSIONS',
    'MESSAGES',
    'OUTCOME_ENGAGEMENT'
]

PRIORITY_ACTIONS = [
    'onsite_conversion.messaging_conversation_started_7d',
    'onsite_conversion.messaging_conversation_started_1d',
    'lead',
    'leads',
    'offsite_conversion.fb_pixel_lead',
    'purchase',
    'initiate_checkout',
    'add_to_cart',
    'contact',
    'schedule',
    'submit_application',
    'link_click', # Fallback
    'post_engagement', # Fallback
    'page_engagement'
]

def process_actions(actions, objective):
    print(f"Testing with Objective: '{objective}'")
    action_map = {a.get('action_type'): float(a.get('value', 0)) for a in actions}
    print(f"Action Map: {action_map}")
    
    for action_type in PRIORITY_ACTIONS:
        if action_type in action_map:
            # Check strict match
            if action_type in ['link_click', 'post_engagement', 'page_engagement']:
                if objective and objective in STRICT_OBJECTIVES:
                    print(f"  Skipping fallback '{action_type}' because objective '{objective}' is strict.")
                    continue 

            print(f"  Match found: {action_type} = {action_map[action_type]}")
            return (float(action_map[action_type]), action_type)
            
    print("  No match found.")
    return (0.0, None)

# Test case 1: OUTCOME_ENGAGEMENT with only link_click
actions = [{'action_type': 'link_click', 'value': '16'}]
process_actions(actions, "OUTCOME_ENGAGEMENT")

# Test case 2: OUTCOME_ENGAGEMENT with whitespace?
process_actions(actions, "OUTCOME_ENGAGEMENT ")

# Test case 3: None objective
process_actions(actions, None)
