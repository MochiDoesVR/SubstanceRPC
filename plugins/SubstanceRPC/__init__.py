# System Modules
import os
import time
import math

# Application Modules
from pypresence import Presence
import substance_painter as sp

client_id = "987223765949743105"
RPC = Presence(client_id)

# Setup & Teardown
def start_plugin():
	sp.logging.log(sp.logging.INFO, "Substance RPC", "Warming up, stand by...")

	connections = {
		sp.event.ProjectOpened: update_sp_presence,
		sp.event.ProjectCreated: update_sp_presence,
		sp.event.ProjectAboutToClose: update_sp_presence,
		sp.event.ProjectAboutToSave: update_sp_presence,
		sp.event.BakingProcessAboutToStart: start_compute_bake,
		sp.event.BakingProcessProgress: update_compute_bake,
		sp.event.BakingProcessEnded: end_compute_bake,
		sp.event.LayerStacksModelDataChanged: update_sp_presence,
	}

	for event, callback in connections.items():
		sp.event.DISPATCHER.connect(event, callback)
	sp.logging.log(sp.logging.INFO, "Substance RPC", "Registered application host callbacks.")

	sp.logging.log(sp.logging.INFO, "Substance RPC", "Connecting to Discord client...")
	RPC.connect()
	sp.logging.log(sp.logging.INFO, "Substance RPC", "Connected to Discord.")

	sp.logging.log(sp.logging.INFO, "Substance RPC", "Ready.")
	update_sp_presence()
def close_plugin():
	RPC.close()
	sp.logging.log(sp.logging.INFO, "Substance RPC", "Shutting down...")

compute_state = False
compute_progress = 0.0

last_update_time = 0.0

def start_compute_bake(e):
	global compute_state
	compute_state = 2
	update_sp_presence()
def update_compute_bake(e):
	global compute_progress
	global compute_state
	compute_state = 1
	compute_progress = e.progress
	update_sp_presence()
def end_compute_bake(e):
	global compute_state
	global compute_progress
	compute_state = 0
	compute_progress = 0.0
	update_sp_presence()

def update_sp_presence(e = None):
	global last_update_time

	if last_update_time - time.time() < 0:
		last_update_time = time.time() + 5.0

		if sp.project.is_open():
			match sp.ui.get_current_mode():
				case 1:
					# Paint Mode
					update_rpc_paintmode()
				case 2:
					# Render Mode
					update_rpc_rendermode()
				case 4:
					# Bake Mode
					update_rpc_bakemode()
				case _:
					sp.logging.log(sp.logging.INFO, "Substance RPC", f'Unknown UIMode ({sp.ui.get_current_mode()}) Active???')
		else:
			update_rpc_noproject()

def update_rpc_bakemode():
	file_name = sp.project.name()
	app_version = sp.application.version()

	if compute_state == 0:
		bake_state = f'Baking || Idle'
	elif compute_state == 1:
		bake_state = f'Baking || Computing... ({math.floor(compute_progress * 100)}%)'
	else:
		bake_state = f'Baking || Warming up...'

	RPC.update(details = f'{file_name}.spp',
			   state = bake_state,
			   large_image='app_icon',
			   small_image='sp_mode_bake',
			   large_text=f'Substance Painter v{app_version} | Substance RPC v1.1.0',
			   small_text='Baking Mode'
			   )
def update_rpc_paintmode():
	file_name = sp.project.name()
	stack = sp.textureset.get_active_stack()
	selection_string = get_node_selection_string(stack)

	app_version = sp.application.version()

	RPC.update(details = f'{file_name}.spp',
			   state = f'Editing {stack.material().name()} || {selection_string}',
			   large_image='app_icon',
			   small_image='sp_mode_paint',
			   large_text=f'Substance Painter v{app_version} | Substance RPC v1.1.0',
			   small_text='Paint Mode'
			   )
def update_rpc_rendermode():
	file_name = sp.project.name()
	app_version = sp.application.version()

	RPC.update(details=f'{file_name}.spp',
			   state='Rendering with NVIDIA® Iray®',
			   large_image='app_icon',
			   small_image='sp_mode_render',
			   large_text=f'Substance Painter v{app_version} | Substance RPC v1.1.0',
			   small_text='NVIDIA® Iray® Preview'
			   )
def update_rpc_noproject():
	app_version = sp.application.version()

	RPC.update(details = f'No Project Open',
			   state = f'Jarvis, touch this man inappropriately.',
			   large_image='app_icon',
			   #small_image='sp_mode_paint',
			   large_text=f'Substance Painter v{app_version} | Substance RPC v1.1.0',
			   small_text='Paint Mode'
			   )

# Helpers
def get_node_selection_string(stack):
	selected_nodes = sp.layerstack.get_selected_nodes(stack)

	if len(selected_nodes) > 1:
		return f'{len(selected_nodes)} Layers'
	elif len(selected_nodes) == 1:
		return selected_nodes[0].get_name()
	elif len(selected_nodes) == 0:
		return "No Layers"

	return "No Layers"

# Plugin Startup
if __name__ == "__main__":
	start_plugin()