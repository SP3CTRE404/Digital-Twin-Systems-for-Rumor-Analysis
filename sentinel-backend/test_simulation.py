"""Test the advanced digital twin simulation"""
from advanced_simulator import run_digital_twin

def main():
    # Test rumor with varying sentiment/stance potential
    test_rumor = "Breaking: Scientists discover a new variant of COVID-19 that spreads through digital devices!"
    
    print("\nRunning advanced digital twin simulation...")
    results = run_digital_twin(
        rumor_text=test_rumor,
        num_nodes=50,  # Smaller network for testing
        edge_prob=0.05,
        spread_prob=0.3,
        steps=8
    )
    
    print("\nSimulation Results:")
    print(f"- Final Coverage: {results['final_coverage']:.2%}")
    print(f"- Total Comments Generated: {sum(len(comments) for comments in results['step_comments'])}")
    
    # Analyze network evolution
    print("\nNetwork Evolution:")
    for step, metrics in enumerate(results['step_metrics']):
        print(f"\nStep {step}:")
        print(f"- Active Users: {metrics['active_count']}")
        print(f"- Network Density: {metrics['density']:.3f}")
        print(f"- Harm Score: {metrics.get('harm_score', 0):.3f}")
        if step > 0:  # Calculate growth rate
            prev_active = results['step_metrics'][step-1]['active_count']
            growth = (metrics['active_count'] - prev_active) / prev_active if prev_active > 0 else 0
            print(f"- Growth Rate: {growth:+.1%}")
    
    # Print sample comments showing different user types and stances
    print("\nSample Comments from First Spread:")
    seen_types = set()
    for comments in results['step_comments']:
        for comment in comments:
            user_type = comment['user']['type']
            if user_type not in seen_types:
                seen_types.add(user_type)
                print(f"\n[{user_type.title()} User]")
                print(f"Comment: {comment['text']}")
                print(f"Stance: {comment['metadata']['stance']}")
            if len(seen_types) >= 4:  # Show one example of each user type
                break
        if len(seen_types) >= 4:
            break
    
    print("\nVisualization Files:")
    print("1. Network Evolution Steps:")
    for vis_path in results['visualizations']['steps']:
        print(f"   - {vis_path}")
    print("2. Final Analysis:")
    print(f"   - {results['visualizations']['final']}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()