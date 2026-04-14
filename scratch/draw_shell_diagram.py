import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def draw_shell_model():
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Set limits and aspect
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 4 Radii: 4, 3, 2, 1 (draw largest first)
    radii = [4, 3, 2, 1]
    
    for r in radii:
        # Default behavior: all white with black edge
        # Except circle with r=2 which we fill with yellow
        # This will make the ring between r=1 and r=2 yellow
        color = 'white'
        if r == 2:
            color = '#FFFF00' # Bright Yellow
            
        circle = patches.Circle((0, 0), r, facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(circle)

    # Origin point i
    ax.scatter(0, 0, color='black', s=60, zorder=10)
    ax.text(0.1, 0.2, r'$i$', fontsize=20, fontweight='bold', zorder=11)
    
    # Labels for bins
    # Label the yellow area as bin_k
    ax.annotate(r'$bin_k$', xy=(1.2, 0.8), xytext=(3.5, 2),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=10),
                fontsize=22, fontweight='bold')
    
    # Circle index labels (optional but clear)
    ax.text(0.5, -0.2, 'bin 1', fontsize=12, ha='center', fontweight='bold')
    ax.text(1.5, -0.2, 'bin 2', fontsize=12, ha='center', fontweight='bold')
    ax.text(2.5, -0.2, 'bin 3', fontsize=12, ha='center', fontweight='bold')
    ax.text(3.5, -0.2, 'bin 4', fontsize=12, ha='center', fontweight='bold')

    plt.tight_layout()
    
    # Save image
    output_path = os.path.join(os.getcwd(), 'shell_model_diagram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
    print(f"Image updated and saved to {output_path}")

import numpy as np

def draw_intra_bin_model():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    radii = [4, 3, 2, 1]
    for r in radii:
        color = 'white'
        if r == 2:
            color = '#FFFF00' # Bright Yellow
        circle = patches.Circle((0, 0), r, facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(circle)

    # Add 3 black dots (destinations j) inside the yellow ring (1 < r < 2)
    num_dots = 3
    dots_x = [1.5, -1.2, 0.5]
    dots_y = [0.5, 1.1, -1.6]
    
    ax.scatter(dots_x, dots_y, color='black', s=80, zorder=10)
    
    # Label the dots as j_1, j_2, j_3
    labels = [r'$j_1$', r'$j_2$', r'$j_3$']
    for i, label in enumerate(labels):
        ax.text(dots_x[i]+0.2, dots_y[i]+0.2, label, fontsize=20, fontweight='bold', zorder=11)

    # Origin point i
    ax.scatter(0, 0, color='black', s=80, zorder=10)
    ax.text(0.1, 0.3, r'$i$', fontsize=24, fontweight='bold', zorder=11)

    plt.tight_layout()
    output_path = os.path.join(os.getcwd(), 'intra_bin_allocation_diagram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
    print(f"Intra-bin Image updated with 3 points and saved to {output_path}")

if __name__ == "__main__":
    draw_shell_model()
    draw_intra_bin_model()
