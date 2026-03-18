from graphviz import Digraph

# Create diagram
dot = Digraph(format='png')
dot.attr(rankdir='LR', size='8,5')

# Nodes
dot.node('A', 'Arduino UNO')
dot.node('S', 'Servo Motor')
dot.node('L', 'Level Sensor')

# Power connections
dot.edge('A', 'S', label='5V')
dot.edge('A', 'L', label='5V')

# Ground connections
dot.edge('A', 'S', label='GND')
dot.edge('A', 'L', label='GND')

# Signal connections
dot.edge('A', 'S', label='Pin 9 (PWM)')
dot.edge('L', 'A', label='Pin 2 (Input)')

# Save diagram
dot.render('circuit_diagram', view=False)

print("✅ Circuit diagram generated as circuit_diagram.png")
