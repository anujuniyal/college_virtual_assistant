#!/usr/bin/env python3
"""
Fix Duplicate Routes Issue
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def find_duplicate_routes():
    """Find and analyze duplicate routes"""
    print("=== ANALYZING DUPLICATE ROUTES ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        # Collect all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'rule': rule.rule,
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'blueprint': rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'app'
            })
        
        # Find duplicates
        rule_counts = {}
        for route in routes:
            rule_key = route['rule']
            if rule_key not in rule_counts:
                rule_counts[rule_key] = []
            rule_counts[rule_key].append(route)
        
        duplicates = {k: v for k, v in rule_counts.items() if len(v) > 1}
        
        print(f"\nFound {len(duplicates)} duplicate route groups:")
        
        for rule, route_list in duplicates.items():
            print(f"\nRoute: {rule}")
            for i, route_info in enumerate(route_list, 1):
                print(f"  {i}. Endpoint: {route_info['endpoint']}")
                print(f"     Blueprint: {route_info['blueprint']}")
                print(f"     Methods: {route_info['methods']}")
        
        return duplicates

def check_blueprint_registration():
    """Check how blueprints are registered"""
    print(f"\n=== CHECKING BLUEPRINT REGISTRATION ===")
    
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print(f"Registered blueprints:")
        for name, blueprint in app.blueprints.items():
            print(f"  {name}: {blueprint}")
        
        print(f"\nBlueprint routes:")
        blueprint_routes = {}
        for rule in app.url_map.iter_rules():
            blueprint_name = rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'app'
            if blueprint_name not in blueprint_routes:
                blueprint_routes[blueprint_name] = []
            blueprint_routes[blueprint_name].append(rule.rule)
        
        for blueprint, routes in blueprint_routes.items():
            print(f"\n{blueprint}: {len(routes)} routes")
            for route in sorted(routes)[:5]:  # Show first 5 routes
                print(f"  {route}")
            if len(routes) > 5:
                print(f"  ... and {len(routes) - 5} more")

def identify_conflicts():
    """Identify specific conflicts and suggest fixes"""
    print(f"\n=== IDENTIFYING CONFLICTS ===")
    
    duplicates = find_duplicate_routes()
    
    print(f"\nCOMMON CONFLICTS:")
    
    # Check for routes.py vs blueprint conflicts
    conflicts = []
    for rule, route_list in duplicates.items():
        blueprints = set(route['blueprint'] for route in route_list)
        if len(blueprints) > 1:
            conflicts.append({
                'route': rule,
                'blueprints': blueprints,
                'endpoints': [route['endpoint'] for route in route_list]
            })
    
    print(f"\nBlueprint conflicts found: {len(conflicts)}")
    for conflict in conflicts:
        print(f"\nRoute: {conflict['route']}")
        print(f"Conflicting blueprints: {conflict['blueprints']}")
        print(f"Endpoints: {conflict['endpoints']}")
    
    return conflicts

def main():
    """Main function to analyze and suggest fixes"""
    print("DUPLICATE ROUTES ANALYSIS")
    print("=" * 50)
    
    try:
        # Analyze duplicates
        duplicates = find_duplicate_routes()
        
        # Check blueprint registration
        check_blueprint_registration()
        
        # Identify conflicts
        conflicts = identify_conflicts()
        
        print(f"\n" + "=" * 50)
        print("ANALYSIS COMPLETE")
        
        print(f"\nSUGGESTED FIXES:")
        print(f"1. Remove duplicate route definitions in routes.py")
        print(f"2. Keep only blueprint-based routes")
        print(f"3. Update route registration order")
        print(f"4. Check for conflicting URL patterns")
        
        print(f"\nSPECIFIC ACTIONS NEEDED:")
        print(f"1. Review routes.py for duplicate admin routes")
        print(f"2. Review routes.py for duplicate auth routes")
        print(f"3. Ensure blueprints are registered correctly")
        print(f"4. Test after removing duplicates")
        
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
