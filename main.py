import pygame, sys, math, random, json, os

# COLORS
COLOR_BG:tuple = (70, 70, 70)

# SPRITES
ORIGINAL_SPRITE_SIZE:int = 16
SPRITE_SIZE:int = 32
BOMB_AMOUNT:int = 40

SCREEN_WIDTH:int = 544
SCREEN_HEIGHT:int = 663 
MENU_HEIGHT:int = 363

BUTTON_WIDTH:int = 200
BUTTON_HEIGHT:int = 55

#border size = (544, 663)
CELL_BORDER_X = 16
CELL_BORDER_Y = 135


class SpriteSheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert()


    def image_at(self, rectangle, colorkey = None):
        """Load a specific image from a specific rectangle."""
        # Loads image from x, y, x+offset, y+offset.
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if (colorkey != None):
            if (colorkey == -1):
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects, colorkey = None):
        """Load a whole bunch of images and return them as a list."""
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect, image_count, colorkey = None):
        """Load a whole strip of images, and return them as a list."""
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)
  


class Timer:
    def __init__(self, autostart=False):
        self.start_time = 0
        self.max_time_ms = 999*1000
        self.current_time = 0
        self.active = False
        if autostart:
            self.activate()

    def check_active(self):
        if self.active:
            return True
        else:
            return False

    def activate(self):
        if not self.check_active():
            self.active = True
            self.start_time = pygame.time.get_ticks()
            print("Timer Activated.")

    def deactivate(self):
        if self.check_active():
            self.active = False
            self.start_time = 0
            print("Timer Deactivated.")

    def update(self) -> int:
        if self.check_active():
            self.current_time = pygame.time.get_ticks() - self.start_time
            #print(self.current_time)
            if (self.current_time) >= self.max_time_ms:
                self.deactivate()
        return self.current_time



class OptionBox():
    def __init__(self, x, y, w, h, color, highlight_color, font, option_list, selected=0):
        self.color = color
        self.highlight_color = highlight_color
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list
        self.selected = selected
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1
        self.mouse_handled = False

    def draw(self, surf):
        pygame.draw.rect(surf, self.highlight_color if self.menu_active else self.color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[self.selected], 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center = self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i+1) * self.rect.height
                pygame.draw.rect(surf, self.highlight_color if i == self.active_option else self.color, rect)
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center = rect.center))
            outer_rect = (self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)

    def update(self):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)
        
        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i+1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        if (pygame.mouse.get_pressed()[0]) and not self.mouse_handled:
            self.mouse_handled = True
            if self.menu_active:
                self.draw_menu = not self.draw_menu
            elif self.draw_menu and self.active_option >= 0:
                self.selected = self.active_option
                self.draw_menu = False
                return self.active_option
            
        if not pygame.mouse.get_pressed()[0]:
            self.mouse_handled = False
        
        return -1



class Settings:
    def __init__(self, filename):
        self.file = filename
        self.data = {}
        self.style_string = 'style'
        self.update()

    def writeSetting(self, title, data):
        self.data[title] = data

    def readSetting(self, title):
        if self.data[title]:
            return self.data[title]
        else:
            return None

    def checkfile(self):
        if (os.path.isfile(self.file)):
            return True
        return False

    def save_settings(self):
        if self.checkfile():
            with open(self.file, 'w') as wfp:
                wfp.write(json.dumps(self.data))
            return True
        else:
            return False

    def load_settings(self):
        data = {}
        if self.checkfile():
            with open(self.file, 'r') as rfp:
                data = json.loads(rfp.read())
            return data
        else:
            return data

    def update(self):
        self.data = self.load_settings()

    def get_style(self) -> tuple:
        style = self.data[self.style_string]
        number = 0
        face = 0
        border = 0
        if style == 3:
            number = 1
        elif style == 4:
            number = 2
            face = 1
            border = 1
        elif style == 6:
            number = 1
        elif style == 7:
            number = 2
            face = 1
            border = 1

        ret_tup = (style, number, face, border)
        print(ret_tup
              )
        return ret_tup


class Cell:
    def __init__(self, starting_img, start_x=0, start_y=0) -> None:
        self.x = start_x
        self.y = start_y
        self.image = starting_img
        self.rect = self.collide_box_l()
        self.is_bomb = False
        self.is_flagged = False
        self.is_revealed = False
        self.state = '0'
        self.left_handled = False
        self.right_handled = False

    def collide_box_l(self) -> object:
        box_x = self.x*SPRITE_SIZE+CELL_BORDER_X
        box_y = self.y*SPRITE_SIZE+CELL_BORDER_Y
        return pygame.Rect(box_x, box_y, SPRITE_SIZE, SPRITE_SIZE)

    def collide_box(self, components:tuple, offsets:tuple=(0,0)) -> object:   
        return pygame.Rect(self.x+offsets[0], self.y+offsets[1], components[0], components[1]) 
    
    def update_rect_components(self, components, offsets=(0,0)):
        self.rect = self.collide_box(components, offsets)

    def get_mouse(self, pos, collide_rect):
        left_action = False
        right_action = False

        if collide_rect.collidepoint(pos):
            if (pygame.mouse.get_pressed()[0] == True) and (self.is_flagged == False) and (self.left_handled == False):
                self.left_handled = True
                left_action = True

            if (pygame.mouse.get_pressed()[2] == True) and (self.is_revealed == False) and (self.right_handled == False):
                self.right_handled = True
                right_action = True

        if pygame.mouse.get_pressed()[0] == False:
            self.left_handled = False

        if pygame.mouse.get_pressed()[2] == False:
            self.right_handled = False

        return left_action, right_action


class MineField:
    def __init__(self, field_width, field_height, bomb_limit, sprite_imgs):
        self.width = field_width
        self.height = field_height
        self.bomb_limit = bomb_limit
        self.sn_imgs = sprite_imgs
        self.first_click = False
        self.cells = self.create_cell_2d_array()
        self.bombs = self.create_random_bombs()
        self.flags = []
        #self.update()

    def get_flag_count(self):
        fl = len(self.flags)
        return self.bomb_limit-fl

    def create_cell_2d_array(self) -> list:
        cell_2d_array = [[Cell(self.sn_imgs[0], row, col) for row in range(self.width)] for col in range(self.height)]
        return cell_2d_array

    def create_random_bombs(self) -> list:
        bomb_list = []
        for i in range(self.bomb_limit):
            finding = True
            while finding:
                rand_x = random.randrange(self.width)
                rand_y = random.randrange(self.height)            
                rand_cell = self.cells[rand_x][rand_y]
                if rand_cell.is_bomb == False:
                    finding = False

            rand_cell.is_bomb = True
            rand_cell.state = 'x'
            bomb_list.append(rand_cell)

        #print(len(bomb_list))
        return bomb_list


    def reveal_bombs(self, endbomb, sprite_index=5):
        if endbomb in self.bombs:
            endbomb.is_revealed = True
            endbomb.image = self.sn_imgs[6]
            self.bombs.remove(endbomb)
            #print(f"End-Game Bomb - (x:{endbomb.x}, y:{endbomb.y})")

        for bomb_cell in self.bombs:
            bomb_cell.is_revealed = True
            if bomb_cell.is_flagged:
                bomb_cell.image = self.sn_imgs[7]
            else:
                bomb_cell.image = self.sn_imgs[sprite_index]

    def check_neighbor_states(self, row, col) -> None:
        neighbor_bomb_count = 0
        cell = self.cells[row][col]
        if (cell.is_bomb or cell.is_flagged):
            return

        for x_offset in range(-1, 2):
            for y_offset in range(-1, 2):
                i = row + x_offset
                j = col + y_offset
                if (i > -1 and i < self.width and j > -1 and j < self.height):
                    neighbor = self.cells[i][j]
                    if (neighbor.is_bomb):
                        neighbor_bomb_count += 1
                    if (cell.is_revealed and not neighbor.is_bomb):
                        if (cell.state == '0'):
                            if neighbor.is_flagged:
                                neighbor.is_flagged = False
                            if neighbor in self.flags:
                                self.flags.remove(neighbor)

                            neighbor.is_revealed = True

                if (neighbor_bomb_count > 0):
                    cell.state = str(neighbor_bomb_count)


    def handle_mouse(self, cell):
        pos = pygame.mouse.get_pos()
        LB_clicked, RB_clicked = cell.get_mouse(pos, cell.rect)
        if (LB_clicked or RB_clicked) and not self.first_click:
            self.first_click = True

        if LB_clicked:
            cell.is_revealed = True
        elif RB_clicked:
            if cell.is_flagged == True:
                cell.is_flagged = False
            elif cell.is_flagged == False:
                if len(self.flags) < BOMB_AMOUNT:
                    cell.is_flagged = True



    def update_sprite(self, cell):
        sprite_index = 0
        if cell.is_revealed:
            if cell.is_bomb:
                sprite_index = 6
            else:
                if cell.state == '0':
                    sprite_index = 1
                else:
                    sprite_index = 7+int(cell.state)
        else:
            if cell.is_flagged == True:
                sprite_index = 2
                if cell not in self.flags:
                    self.flags.append(cell)

            elif cell.is_flagged == False:
                if cell in self.flags:
                    self.flags.remove(cell)

        cell.image = self.sn_imgs[sprite_index]


    def update(self) -> None:
        for row in range(self.width):
            for col in range(self.height):
                cell = self.cells[row][col]
                
                self.update_sprite(cell)
                self.handle_mouse(cell)
                self.check_neighbor_states(row, col)
 
    def reset_grid(self):
        self.first_click = False
        self.cells = self.create_cell_2d_array()
        self.bombs = self.create_random_bombs()
        self.flags = []
    
    
        
class Game:
    def __init__(self) -> None:
        self.title = 'Pysweeper!'
        self.debug = False
        self.running = False
        self.is_win = False
        self.is_lose = False
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # (544, 663)
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()    
        self.FPS:int = 20
        pygame.init()
        self.face_scaled_sprite_size = (48, 48)
        self.face_x = 16+(512/2)-(self.face_scaled_sprite_size[0]/2)
        self.face_y = 16+(103/2)-(self.face_scaled_sprite_size[1]/2)
        self.pixel_sans_bold = pygame.font.Font("assets/fonts/PixeloidSans-Bold.ttf", 20)
        self.pixel_sans = pygame.font.Font("assets/fonts/PixeloidSans.ttf", 16)
        self.pixel_sans_small = pygame.font.Font("assets/fonts/PixeloidSans-Bold.ttf", 12)
        self.settings = Settings("settings.json")
        self.load_styled_sprites()
        self.timer = Timer()
        self.menu_state = 'menu'
        self.face_status = 0
        self.face_clicked = False
        self.digit_scaled_sprite_size = (39, 69)
        self.digit_length = 3
        self.digit_time_stack = ''
        self.digit_flag_stack = ''
        self.style_names = ["PMMine (Mine 2.0)", "WinMine 2.6-2.9", "Windows 95/98", "Windows 3.1/2000", "Windows 3.1/2000 Monochrome", "Prato Fiorito 2000", "Prato Fiorito XP", "Prato Fiorito Monochrome"]
        self.style_optionbox = OptionBox(SCREEN_WIDTH/2-95, SCREEN_HEIGHT/2-121, 250, 25, (255, 255, 255), (210, 210, 205), self.pixel_sans_small, self.style_names)

    def load_styled_sprites(self):
        style_settings = self.settings.get_style()
        self.sprite_sheet = SpriteSheet(f"assets/tiles/tiles-{style_settings[0]}.png")
        self.digits_sheet = SpriteSheet(f"assets/numbers/numbers-{style_settings[1]}.png")
        self.face_sheet = SpriteSheet(f"assets/faces/faces-{style_settings[2]}.png")
        self.border_sheet = SpriteSheet(f"assets/borders/border-{style_settings[3]}.png")
        self.menu_sheet = SpriteSheet(f"assets/menus/menu-{style_settings[3]}.png")
        self.menu_button_sheet = SpriteSheet(f"assets/menus/button-{style_settings[3]}.png")
        self.menu_img = self.menu_sheet.image_at((0, 0, SCREEN_WIDTH, MENU_HEIGHT))
        self.border_img = self.border_sheet.image_at(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.button_imgs = self.menu_button_sheet.load_strip(pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT), 2)
        self.sprite_imgs = self.sprite_sheet.load_strip(pygame.Rect(0, 0, 16, 16), 8)
        self.number_imgs = self.sprite_sheet.load_strip(pygame.Rect(0, 16, 16, 16), 8)
        self.face_sprites = self.face_sheet.load_strip(pygame.Rect(0, 0, 24, 24), 5)
        self.digits_sprites = self.digits_sheet.load_strip(pygame.Rect(0, 0, 13, 23), 10)
        self.face_cell = Cell(self.face_sprites[0], self.face_x, self.face_y)
        self.grid = MineField(16, 16, BOMB_AMOUNT, self.sprite_imgs + self.number_imgs)

        
    def check_bombs(self):
        flag_count = 0
        for i in range(len(self.grid.bombs)):
            cell = self.grid.bombs[i]
            if (cell.is_revealed):
                return -1, cell

            if (cell.is_flagged):
                flag_count += 1

        if (self.grid.get_flag_count() == 0) and (flag_count >= BOMB_AMOUNT):
            return 1, None

        return 0, None


    def create_digit_stack(self, src_number):
        str_num = str(src_number)
        chars_needed = self.digit_length-len(str_num)
        _digits = ''

        if chars_needed > 0:
            for z in range(chars_needed):
                _digits += '0'
        _digits += str_num

        return _digits

    def game_timer_update(self) -> int:
        is_active = self.timer.check_active()
        if is_active == True:
            #print('timer update')
            return self.timer.update()
        else: 
            if (self.grid.first_click == True):
                #print('timer created!')
                self.timer.activate()
                return 0
            return self.timer.current_time


    def update_game_board(self) -> None:
        border_px_offset = 35
        digit_flag_stack_pos = (32, 32)
        time = math.floor(self.game_timer_update()/1000)
        #print(time)
        flags = self.grid.get_flag_count()
        if flags < 0:
            flags = 0

        DTs = self.create_digit_stack(time)
        DFs = self.create_digit_stack(flags)
        #print(DFs)
        if self.digit_time_stack != DTs:
            self.digit_time_stack = DTs
        if self.digit_flag_stack != DFs:
            self.digit_flag_stack = DFs

        #draw border
        self.window.blit(self.border_img, (0, 0))

        #draw time 
        for ti in range(self.digit_length):
            t_number = int(self.digit_time_stack[ti])
            t_pos = (border_px_offset+16+(ti*self.digit_scaled_sprite_size[0]), 16+(103/2)-(self.digit_scaled_sprite_size[1]/2))
            t_sprite = self.digits_sprites[t_number]
            t_scaled_sprite = pygame.transform.scale(t_sprite, self.digit_scaled_sprite_size)
            self.window.blit(t_scaled_sprite, t_pos)
            if self.debug: pygame.draw.rect(self.window, (0, 0, 255), pygame.Rect(t_pos, self.digit_scaled_sprite_size), 1)

        #draw flags remaining
        for tf in range(self.digit_length):
            f_number = int(self.digit_flag_stack[tf])
            f_pos = (16+(512-(self.digit_scaled_sprite_size[0]*3))-border_px_offset+(tf*self.digit_scaled_sprite_size[0]), 16+(103/2)-(self.digit_scaled_sprite_size[1]/2))
            f_sprite = self.digits_sprites[f_number]
            f_scaled_sprite = pygame.transform.scale(f_sprite, self.digit_scaled_sprite_size)
            self.window.blit(f_scaled_sprite, f_pos)
            if self.debug: pygame.draw.rect(self.window, (0, 0, 255), pygame.Rect(f_pos, self.digit_scaled_sprite_size), 1)

        #draw reset button
        face_rect = self.face_cell.collide_box(self.face_scaled_sprite_size)
        LB_clicked, RB = self.face_cell.get_mouse(pygame.mouse.get_pos(), face_rect)
        if LB_clicked:
            self.face_status = 1
            #if self.is_win or self.is_lose:
            self.menu_state = 'play'
            self.is_win = False
            self.is_lose = False
            self.grid.reset_grid()
            if self.timer.check_active():
                self.timer.deactivate()
            self.timer.current_time = 0
            #print('Game Reset.')
        else:
            if self.is_win:
                self.face_status = 3
            elif self.is_lose:
                self.face_status = 4
            else:
                self.face_status = 0
            
        self.face_cell.image = self.face_sprites[self.face_status]

        face_scaled_sprite = pygame.transform.scale(self.face_sprites[self.face_status], self.face_scaled_sprite_size)
        self.window.blit(face_scaled_sprite, (self.face_cell.x, self.face_cell.y))
        if self.debug: pygame.draw.rect(self.window, (255, 0, 0), face_rect, 1)


    def draw_cells(self) -> None:
        for r in range(self.grid.width):
            for c in range(self.grid.height):
                cell = self.grid.cells[r][c]
                scaled_sprite = pygame.transform.scale(cell.image, (SPRITE_SIZE, SPRITE_SIZE))
                pos = (cell.x*SPRITE_SIZE+CELL_BORDER_X, cell.y*SPRITE_SIZE+CELL_BORDER_Y)
                self.window.blit(scaled_sprite, pos)
                if self.debug: pygame.draw.rect(self.window, (0, 255, 0), cell.collide_box_l(), 1)
                
    
    def update_options(self):
        x = SCREEN_WIDTH/2
        y = SCREEN_HEIGHT/2 - 201
        self.window.fill(COLOR_BG)
        self.window.blit(self.menu_img, (0, y))
        
        title = "OPTIONS & SETTINGS"
        title_surface = self.pixel_sans_bold.render(title, True, (0, 0, 0))
        self.window.blit(title_surface, (x-title_surface.get_width()/2, y+title_surface.get_height()))

        style_opt = self.pixel_sans.render("Style Version:", True, (0, 0, 0))
        pos = (x-220, y+style_opt.get_height()*4)
        #print(pos)
        self.window.blit(style_opt, pos)
        
        selected_option = self.style_optionbox.update()
        if selected_option >= 0:
            print(f"selected option: \"{self.style_names[selected_option]}\"")
            self.settings.data[self.settings.style_string] = selected_option
            self.load_styled_sprites()
            
        dimensions = (200, 55)
        x = SCREEN_WIDTH/2+45
        y = SCREEN_HEIGHT-250
        back_but = Cell(self.button_imgs[0], x, y)
        back_but.update_rect_components(dimensions)
        is_hovering = back_but.rect.collidepoint(pygame.mouse.get_pos())
        LB_clicked, r = back_but.get_mouse(pygame.mouse.get_pos(), back_but.rect)
        elevation = 0
        if (LB_clicked) or (is_hovering):
            back_but.image = self.button_imgs[1]
            elevation = 2

        self.window.blit(back_but.image, (x, y))
        text_surface = self.pixel_sans_bold.render("Save & Exit", True, (0, 0, 0))
        self.window.blit(text_surface, text_surface.get_rect(center=back_but.rect.center).move(elevation, elevation))
        self.style_optionbox.draw(self.window)
        
        if (LB_clicked):      
            self.settings.save_settings()
            self.menu_state = 'menu'
        
    def buttonpress_play(self):
        #print("PLAY")
        self.menu_state = 'play'
    
    def buttonpress_options(self):
        #print("OPTIONS")
        self.menu_state = 'options'
            
    def buttonpress_exit(self):
        #print("EXIT")
        self.running = False
    
    def update_menu(self):
        x = SCREEN_WIDTH/2
        y = SCREEN_HEIGHT/2 - 201
        self.window.fill(COLOR_BG)
        self.window.blit(self.menu_img, (0, y))
        
        title_surface = self.pixel_sans_bold.render("MINESWEEPER MAIN MENU", True, (0, 0, 0))
        self.window.blit(title_surface, (x-title_surface.get_width()/2, y+title_surface.get_height()))
        
        text = ["PLAY", "OPTIONS", "EXIT"]
        funcs = [self.buttonpress_play, self.buttonpress_options, self.buttonpress_exit]
        button_cells = []
        dimensions = (200, 55)
        x = x - 100
        y = SCREEN_HEIGHT/2 - 70
        cursor_pos = pygame.mouse.get_pos()
        for i in range(3):
            elevation = 0
            c = Cell(self.button_imgs[0], x, y)
            c.update_rect_components(dimensions)
            is_hovering = c.rect.collidepoint(cursor_pos)
            LB_clicked, r = c.get_mouse(cursor_pos, c.rect)
            if (LB_clicked) or (is_hovering):
                c.image = self.button_imgs[1]
                elevation = 2


            self.window.blit(c.image, (x, y))
            text_surface = self.pixel_sans_bold.render(text[i], True, (0, 0, 0))
            self.window.blit(text_surface, text_surface.get_rect(center=c.rect.center).move(elevation, elevation))
            button_cells.append(c)
            y += dimensions[1]
            
            if (LB_clicked):
                funcs[i]()


    def events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.menu_state == 'play':
                    if self.timer.check_active():
                        self.timer.deactivate()
                    self.menu_state = 'menu'


    def start(self) -> None:
        self.running = True
        self.is_win = False
        self.is_lose = False
        while (self.running):
            self.clock.tick(self.FPS)
            self.events()
            
            if self.menu_state == 'menu':
                self.update_menu()

            elif self.menu_state == 'play':
                self.grid.update()
                self.update_game_board()
                self.draw_cells()
                win_check, endbomb = self.check_bombs()
                if win_check == 1:
                    self.is_win = True
                    self.is_lose = False
                    self.grid.first_click = False
                    self.menu_state = 'over'
                    self.timer.deactivate()
                    self.grid.reveal_bombs(None, 7)
                elif win_check == -1:
                    self.is_lose = True
                    self.is_win = False
                    self.grid.first_click = False
                    self.menu_state = 'over'
                    self.timer.deactivate()
                    self.grid.reveal_bombs(endbomb, 5)
            
            elif self.menu_state == 'options':
                self.update_options()
                
            elif self.menu_state == 'over':
                self.update_game_board()
                self.draw_cells()
            
            pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.debug = False
    game.start()
    pygame.quit()
    
sys.exit()