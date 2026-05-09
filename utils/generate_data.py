import pandas as pd
import numpy as np
import random

def generate_realistic_data(n=1000):
    np.random.seed(42)
    
    # Generate features
    cgpa = np.random.uniform(6.0, 9.8, n)
    aptitude = np.random.randint(40, 100, n)
    coding = np.random.randint(30, 100, n)
    comms = np.random.randint(3, 10, n)
    projects = np.random.randint(0, 6, n)
    technical = np.random.randint(1, 15, n)
    
    # Calculate a weighted score for placement
    # CGPA (30%), Aptitude (20%), Coding (25%), Comms (10%), Projects (10%), Technical (5%)
    weighted_score = (
        (cgpa / 10 * 30) + 
        (aptitude / 100 * 20) + 
        (coding / 100 * 25) + 
        (comms / 10 * 10) + 
        (projects / 5 * 10) + 
        (technical / 15 * 5)
    )
    
    # Add some randomness to make it realistic
    noise = np.random.normal(0, 5, n)
    final_score = weighted_score + noise
    
    # Threshold for placement
    placed = (final_score > 60).astype(int)
    
    df = pd.DataFrame({
        'CGPA': np.round(cgpa, 2),
        'AptitudeScore': aptitude,
        'CodingScore': coding,
        'CommunicationSkills': comms,
        'Projects': projects,
        'TechnicalSkills': technical,
        'Placed': placed
    })
    
    df.to_csv('datasets/placement_data.csv', index=False)
    print(f"Generated {n} realistic records in datasets/placement_data.csv")

if __name__ == "__main__":
    generate_realistic_data()
