from typing import List, Dict

def process_actions(actions: List[Dict]) -> tuple:
    if not actions:
        return (0, None)
    
    # Priority list (same as in sync script)
    PRIORITY_ACTIONS = [
        'onsite_conversion.messaging_conversation_started_7d',
        'onsite_conversion.messaging_conversation_started_1d',
        'leads',
        'purchase',
        'initiate_checkout',
        'add_to_cart',
        'contact',
        'schedule',
        'submit_application',
        'link_click',
        'post_engagement',
        'page_engagement'
    ]

    action_map = {a.get('action_type'): float(a.get('value', 0)) for a in actions}
    
    resultado_valor = 0.0
    resultado_nome = None

    for action_type in PRIORITY_ACTIONS:
        if action_type in action_map:
            resultado_valor = action_map[action_type]
            resultado_nome = action_type
            break
            
    if resultado_nome is None and action_map:
        resultado_nome = max(action_map, key=action_map.get)
        resultado_valor = action_map[resultado_nome]

    return (float(resultado_valor), resultado_nome)

# Test Data mimicking inflated leads scenario
test_actions = [
    {'action_type': 'page_engagement', 'value': '5000'},
    {'action_type': 'post_engagement', 'value': '4000'},
    {'action_type': 'onsite_conversion.messaging_conversation_started_7d', 'value': '15'},
    {'action_type': 'link_click', 'value': '100'}
]

val, name = process_actions(test_actions)
print(f"Result: {val} (Type: {name})")
