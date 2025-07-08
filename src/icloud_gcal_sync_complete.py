        }
        
        if sync_manager.last_sync_time:
            next_sync = sync_manager.last_sync_time + timedelta(hours=status["sync_interval_hours"])
            status["next_sync_time"] = next_sync.isoformat()
            status["time_until_next_sync_hours"] = (next_sync - datetime.now()).total_seconds() / 3600
        
        return [
            types.TextContent(
                type="text",
                text=f"Current sync status:\\n\\n" + json.dumps(status, indent=2)
            )
        ]
    
    elif name == "reset_sync_state":
        confirm = arguments.get("confirm", False)
        if not confirm:
            return [
                types.TextContent(
                    type="text",
                    text="Reset not confirmed. Set 'confirm' to true to reset sync state."
                )
            ]
        
        sync_manager.synced_events.clear()
        sync_manager.last_sync_time = None
        sync_manager.save_synced_events()
        
        return [
            types.TextContent(
                type="text",
                text="Sync state reset. All events will be considered new on next sync."
            )
        ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Auto-start sync if configured
        if sync_manager.sync_config.get('auto_start_sync', False):
            await sync_manager.start_sync_scheduler()
        
        try:
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="icloud-gcal-sync",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
        finally:
            # Clean shutdown
            await sync_manager.stop_sync_scheduler()

if __name__ == "__main__":
    asyncio.run(main())