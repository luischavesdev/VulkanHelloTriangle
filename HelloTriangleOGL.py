import pygame as pg

from numpy import array

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL import shaders


class Engine:
    def __init__(self):
        # Initialize general variables
        self.window_size = (640, 480)
        self.size_of_float = 4

        self.triangle_vertices = None

        self.triangle_vao = None
        self.triangle_vbo = None

        self.shader_program = None
        self.clock = pg.time.Clock()

        # Initiate Pygame and its window 
        pg.init()
        pg.display.set_mode(self.window_size, pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE)

        # Setup OpenGL general parameters
        glClearColor(1.0, 0.5, 0.25, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_LIGHTING)


        # Create and bind VAO
        self.triangle_vao = glGenVertexArrays(1)
        glBindVertexArray(self.triangle_vao)

        # Create and bind VBO  
        self.triangle_vertices = array([
                [0, 0.5, 1, 0, 0],
                [0.5, -0.5, 0, 1, 0],
                [-0.5, -0.5, 0, 0, 1]
            ], 'f')

        self.triangle_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.triangle_vbo)
        glBufferData(GL_ARRAY_BUFFER, self.size_of_float * self.triangle_vertices.size, self.triangle_vertices, GL_STATIC_DRAW)

        # Take care of shaders
        self.initShaders()

        # Find by name and setup vertex attributes that are going to be used in vertex shader
        posAttributeIndex = glGetAttribLocation(self.shader_program, "position")
        glEnableVertexAttribArray(posAttributeIndex)
        glVertexAttribPointer(posAttributeIndex, 2, GL_FLOAT, GL_FALSE, 5 * self.size_of_float, None)

        colorAttributeIndex = glGetAttribLocation(self.shader_program, "color")
        glEnableVertexAttribArray(colorAttributeIndex)
        glVertexAttribPointer(colorAttributeIndex, 3, GL_FLOAT, GL_FALSE, 5 * self.size_of_float, ctypes.c_void_p(2 * self.size_of_float))

        # Run loop
        self.run()

    def initShaders(self):
        # Vertex shader source
        vertex_shader = shaders.compileShader("""#version 330
            in vec2 position;
            in vec3 color;

            out vec3 vColor;

            void main() {
                gl_Position = vec4(position, 0.0, 1.0);
                vColor = vec3(color);
            }
        """, GL_VERTEX_SHADER)

        # Verify vertex shader compilation
        result = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
        if not (result):
            raise RuntimeError(glGetShaderInfoLog(vertex_shader))

        # Fragment shader source
        fragment_shader = shaders.compileShader("""#version 330
            in vec3 vColor;
            out vec4 out_color;

            void main() {
                out_color = vec4(vColor,1); 
            }
        """, GL_FRAGMENT_SHADER)

        # Verify fragment shader compilation
        result = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
        if not (result):
            raise RuntimeError(glGetShaderInfoLog(fragment_shader))

        # Compile and verify the shader program, which includes the two configured shaders
        self.shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
        result = glGetProgramiv(self.shader_program, GL_LINK_STATUS)
        if not (result):
            raise RuntimeError(glGetProgramInfoLog(self.shader_program))

        # Bind the program that was just created
        glUseProgram(self.shader_program)

    def process_events(self, keys):
        # Process keys that are being pressed and perform some actions
        if keys[pg.K_UP]:

            # change uniforms, for example, while running
           pass
    
    def run(self):
        while True:
            delta = self.clock.tick(60) # This ensures that this runs at 60 frames per second
            self.process_events(pg.key.get_pressed())  # Checking already pressed keys

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()

            # Render
            glClear(GL_COLOR_BUFFER_BIT)
            glDrawArrays(GL_TRIANGLES, 0, 3)
            pg.display.flip()


# MAIN
my_engine = Engine()