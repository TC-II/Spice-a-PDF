import svgwrite
import re
import os
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0

font_path = os.path.join('fonts', 'cmunrm.ttf')


class Component:
    def __init__(slf, component_type, position, orientation, attributes, windows):
        slf.component_type = component_type
        slf.position = position
        slf.orientation = orientation
        slf.attributes = attributes
        slf.windows = windows

    def draw(slf, dwg):
        raise NotImplementedError

    def adjust_coordinates_for_orientation_and_alignment(slf, x, y, alignment):
        if alignment == "Left":
            if slf.orientation in ["R0", "M0"]:
                y += 6.5
                return x, y
            elif slf.orientation in ["R180", "M180"]:
                y -= 7
                return -x, -y
        elif alignment == "VTop":
            if slf.orientation in ["R90", "M90"]:
                x += 22
            elif slf.orientation == "R270":
                x += 6
        elif alignment == "VBottom":
            if slf.orientation in ["R90", "M90"]:
                x -= 6
            elif slf.orientation in ["R270", "M270"]:
                x -= 18

        return slf.rotate_coordinates(x, y)

    def rotate_coordinates(slf, x, y):
        if slf.orientation in ["R0", "M0"]:
            return x, y
        elif slf.orientation in ["R90", "M90"]:
            return -y, x
        elif slf.orientation in ["R180", "M180"]:
            return -x, -y
        elif slf.orientation in ["R270", "M270"]:
            return y, -x
                

    def add_text(slf, dwg, x, y, window, text, size = "20px", angle = 0):
        coords = slf.adjust_coordinates_for_orientation_and_alignment(window[0], window[1], window[2])
        if coords is None:
            raise ValueError("Coords cannot be None. Please check the window value.")
        
        if window[2] in ["VTop", "VBottom"]:
            dwg.add(dwg.text(text, insert=(x + coords[0], y + coords[1]), font_family="CMU Serif", font_size=size, text_anchor="middle"))
        else:
            text_element = dwg.text(text, insert=(x + coords[0], y + coords[1]), font_family="CMU Serif", font_size=size, text_anchor="end" if (slf.orientation == "R90" or slf.orientation == "R180") else "start")
            text_element.rotate(-angle, center = (x + coords[0], y + coords[1]))
            dwg.add(text_element)

    def draw_image_with_rotation(slf, dwg, href):
        x, y = slf.position
        image = svgwrite.image.Image(href=href, insert=(x, y))

        if slf.orientation.startswith('M'):
            # Espejado
            angle = int(slf.orientation[1:])
            transform = f"scale(-1, 1) translate({-2 * x}, 0) rotate({angle}, {x}, {y})"
        else:
            # Rotación normal
            angle = int(slf.orientation[1:])
            transform = f"rotate({angle}, {x}, {y})"
        
        image['transform'] = transform
        dwg.add(image)

class Resistor(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/ress.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type))

class Pot(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/pot.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type))

class Capacitor(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/cap.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1] - 8, slf.windows.get(0, (24, 8, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1] + 5, slf.windows.get(3, (24, 56, "Left")), slf.attributes.get("Value", slf.component_type))

class Inductor(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/ind.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type))

class OpAmp(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/OA.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (24, 8, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (-176, 32, "Left")), slf.attributes.get("Value", slf.component_type), "9px",  (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(123, (-176, 48, "Left")), slf.attributes.get("Value2", slf.component_type), "9px", (int(slf.orientation[1:]))%180)

class TL082(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/TL082.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (24, 8, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)

class Flag(Component):
    def draw(slf, dwg):
        if(slf.attributes.get("Value", slf.component_type) == "0"):
            slf.draw_image_with_rotation(dwg, 'Skins/Default/GND.svg')
        else:
            slf.draw_image_with_rotation(dwg, 'Skins/Default/FLAG.svg')
            place_text_according_to_cable(slf.position, slf.attributes.get("Value", slf.component_type), wires, dwg)

class Voltage(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/voltage.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type))

class NPN(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/NPN.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1] - 8, slf.windows.get(0, (56, 32, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1] + 5, slf.windows.get(3, (56, 68, "Left")), slf.attributes.get("Value", " "))

class PNP(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/PNP.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1] - 8, slf.windows.get(0, (56, 32, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1] + 5, slf.windows.get(3, (56, 68, "Left")), slf.attributes.get("Value", " "))

class Not(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/74HCU04 Not.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (24, 8, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (-176, 32, "Left")), slf.attributes.get("Value", slf.component_type), "9px",  (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(123, (-176, 48, "Left")), slf.attributes.get("Value2", slf.component_type), "9px", (int(slf.orientation[1:]))%180)

class Amp_Current(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/Amp_Current.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type), angle = (int(slf.orientation[1:]))%180)

class Amp_Transimpedance(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/Amp_Transimpedance.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type), angle = (int(slf.orientation[1:]))%180)

class Ampmeter(Component):
    def draw(slf, dwg): 
        slf.draw_image_with_rotation(dwg, 'Skins/Default/ampmeter.svg')
        if (slf.orientation == "R0" or slf.orientation == "R180"):
            offset = 7
        else:
            offset = 0
        slf.add_text(dwg, slf.position[0] + offset, slf.position[1] + offset, slf.windows.get(0, (-23, 14, "Left")), slf.attributes.get("InstName", ""), angle = 90)

class Arrow(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/arrow.svg')
        offsetx = offset_text(slf, 0, 3, 0, 11)
        offsety = offset_text(slf, 12)
        slf.add_text(dwg, slf.position[0] + offsetx, slf.position[1] + offsety, slf.windows.get(3, (21, -18, "Left")), slf.attributes.get("Value", "Ir"), angle = (int(slf.orientation[1:]))%180)

class Arrow_curve(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/arrow_curve.svg')
        offsetx = offset_text(slf, 3, 7, -3, -9)
        offsety = offset_text(slf, -1, 15, -7, -4)
        slf.add_text(dwg, slf.position[0] + offsetx, slf.position[1] + offsety, slf.windows.get(3, (63, 55, "Left")), slf.attributes.get("Value", "Vr"))

class Bypass(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/bypass.svg')
       
class Current(Component):
    def draw(slf, dwg):

        offset = offset_text(slf, 15, 0, 15, 0)
    
        slf.draw_image_with_rotation(dwg, 'Skins/Default/current.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1] - offset - 3, slf.windows.get(0, (36, 40, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1] - offset, slf.windows.get(3, (36, 76, "Left")), slf.attributes.get("Value", slf.component_type))

class Cell(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/cell.svg')
        slf.add_text(dwg, slf.position[0] - 12, slf.position[1] + 6, slf.windows.get(0, (24, 8, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0] - 12, slf.position[1] - 8, slf.windows.get(3, (24, 56, "Left")), slf.attributes.get("Value", slf.component_type))

class Diode(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/diode.svg')
        slf.add_text(dwg, slf.position[0] + 7, slf.position[1] + 4, slf.windows.get(0, (24, 0, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0] + 7, slf.position[1] - 4, slf.windows.get(3, (24, 64, "Left")), slf.attributes.get("Value", slf.component_type))

class LM311(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/LM311.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (-112, -16, "Left")), slf.attributes.get("InstName", ""), angle = (int(slf.orientation[1:]))%180)
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (-112, 7, "Left")), slf.attributes.get("Value", slf.component_type), angle = (int(slf.orientation[1:]))%180)

class Switch(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/switch.svg')
       
class Zener(Component):
    def draw(slf, dwg):
        slf.draw_image_with_rotation(dwg, 'Skins/Default/zener.svg')
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(0, (24, 0, "Left")), slf.attributes.get("InstName", ""))
        slf.add_text(dwg, slf.position[0], slf.position[1], slf.windows.get(3, (24, 64, "Left")), slf.attributes.get("Value", slf.component_type))

def offset_text (slf, off0 = 0, off90  = 0, off180  = 0, off270  = 0):
    if (slf.orientation == "R0"):
        return  off0
    elif(slf.orientation == "R90"):
        return off90
    elif(slf.orientation == "R180"):
        return off180
    elif(slf.orientation == "R270"):
        return off270
    else:
        return 0


def parse_asc_file(filename):
    wires = []
    components = []
    current_component = None
    windowsize = None

    with open(filename, 'r') as file:
        for line in file:
            parts = line.split()
            if parts[0] == "WIRE":
                x1, y1, x2, y2 = map(int, parts[1:])
                wires.append(((x1, y1), (x2, y2)))
            elif parts[0] == "SYMBOL":
                if current_component:
                    components.append(current_component)
                component_type = parts[1]
                if '\\' in component_type:
                    component_type_parts = component_type.split('\\')
                    # Caso especial: si el nombre del componente termina en "\\"
                    if component_type_parts[-1] == '':
                        component_name = parts[2]
                        coords_and_orientation = parts[3:]
                    else:
                        component_name = component_type_parts[-1].split()[-1]
                        coords_and_orientation = parts[2:]
                else:
                    component_name = component_type
                    coords_and_orientation = parts[2:]

                x, y = map(int, coords_and_orientation[:2])
                orientation = coords_and_orientation[2] if len(coords_and_orientation) > 2 else "R0"
                
                current_component = {"type": component_name, "position": (x, y), "orientation": orientation, "attributes": {}, "windows": {}}
            elif parts[0] == "SYMATTR" and current_component:
                attribute_name = parts[1]
                attribute_value = " ".join(parts[2:])
                current_component["attributes"][attribute_name] = attribute_value
            elif parts[0] == "WINDOW" and current_component:
                window_index = int(parts[1])
                x, y = map(int, parts[2:4])
                alignment = parts[4]
                current_component["windows"][window_index] = (x, y, alignment)
            elif parts[0] == "FLAG":
                x, y = map(int, parts[1:3])
                component_type = "flag"
                orientation = "R0"
                flag = {"type": component_type, "position": (x, y), "orientation": orientation, "attributes": {}, "windows": {}}
                flag["attributes"]["Value"] = parts[3]
                components.append(flag)
            elif parts[0] == 'SHEET':
                windowsize = (parts[2], parts[3])

        if current_component:
            components.append(current_component)

    return wires, components, windowsize

def get_cable_direction(pin_position, cables):
    for (start, end) in cables:
        if pin_position == start:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
        elif pin_position == end:
            dx = start[0] - end[0]
            dy = start[1] - end[1]
        else:
            continue
        
        if dx > 0:
            return "right"
        elif dx < 0:
            return "left"
        elif dy > 0:
            return "down"
        elif dy < 0:
            return "up"
    return None

def place_text_according_to_cable(pin_position, text, cables, dwg, offset=20):
    direction = get_cable_direction(pin_position, cables)
    
    if direction == "up":
        text_position = (pin_position[0], pin_position[1] + offset)
    elif direction == "down":
        text_position = (pin_position[0], pin_position[1] - offset + 10)
    elif direction == "left":
        text_position = (pin_position[0] + offset, pin_position[1] + 5)
    elif direction == "right":
        text_position = (pin_position[0] - offset, pin_position[1] + 5)
    else:
        text_position = pin_position
    
    dwg.add(dwg.text(text, insert=text_position, font_family="CMU Serif", font_size="20px", text_anchor="middle"))

def create_circuit_svg(filename, wires, components):
    dwg = svgwrite.Drawing(filename, size=windowsize, profile='tiny')
    nodes = {}

    # Dibujar cables y detectar nodos
    for (start, end) in wires:
        dwg.add(dwg.line(start=start, end=end, stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=1.5))
        for point in [start, end]:
            if point in nodes:
                nodes[point] += 1
            else:
                nodes[point] = 1

    # Dibujar nodos si se intersectan 3 o más cables
    for point, count in nodes.items():
        if count >= 3:
            dwg.add(dwg.circle(center=point, r=3, fill='black'))

    # Dibujar componentes
    component_objects = {
        "Not": Not,     
        "Amp_Current": Amp_Current,
        "Amp_Transimpedance": Amp_Transimpedance,
        "ampmeter": Ampmeter, 
        "arrow": Arrow,
        "arrow_curve": Arrow_curve,
        "bypass": Bypass,
        "current": Current,
        "cell": Cell,
        "diode": Diode,
        "LM311": LM311,
        "switch": Switch,
        "zener": Zener,
        "res": Resistor,
        "cap": Capacitor,
        "OA_Ideal": OpAmp,
        "flag": Flag,
        "npn": NPN,
        "pnp": PNP,
        "ind": Inductor,
        "pot": Pot,
        "TL082": TL082,
        "voltage": Voltage
    }

    for component in components:
        component_type = component["type"]
        if component_type in component_objects:
            component_obj = component_objects[component_type](
                component_type,
                component["position"],
                component["orientation"],
                component["attributes"],
                component["windows"]
            )
            component_obj.draw(dwg)

    dwg.save()

def modify_svg_font(svg_filename, output_svg_filename, font_name):
    with open(svg_filename, 'r', encoding='utf-8') as file:
        svg_content = file.read()
    
    # Reemplaza cualquier referencia de fuente por CMU Serif
    modified_svg_content = re.sub(r'font-family="[^"]+"', f'font-family="{font_name}"', svg_content)
    
    with open(output_svg_filename, 'w', encoding='utf-8') as file:
        file.write(modified_svg_content)

def svg_to_pdf(svg_filename, pdf_filename):
    # Registrar la fuente CMU Serif
    pdfmetrics.registerFont(TTFont('CMU_Serif', font_path))
    
    # Registrar la fuente con el mapeo de svglib
    from svglib.fonts import register_font
    register_font('CMU_Serif', font_path)
    
    # Leer el dibujo SVG
    drawing = svg2rlg(svg_filename)
    
    # Crear el canvas PDF
    c = canvas.Canvas(pdf_filename, pagesize= windowsize)
    
    # Dibujar el SVG en el PDF
    renderPDF.draw(drawing, c, 0, 0)
    
    # Guardar el PDF
    c.showPage()
    c.save()


# Ejemplo de uso
asc_filename = 'Cables.asc'
modified_svg_filename = 'ModifiedOutput.svg'
svg_filename = 'Output.svg'
pdf_filename = 'Output.pdf'

wires, components, windowsize = parse_asc_file(asc_filename)

create_circuit_svg(svg_filename, wires, components)

# Modifica el SVG para usar CMU Serif
modify_svg_font(svg_filename, modified_svg_filename, 'CMU_Serif')

svg_to_pdf(modified_svg_filename, pdf_filename)
