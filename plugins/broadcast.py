# =============================================================================
#  CipherElite Userbot Plugin
#
#  Plugin Name:    broadcast
#  Author:         CipherElite Dev (@rishabhops)
#  Repository:     https://github.com/rishabhops/CipherElite
#
#  License:        MIT
#
#  IMPORTANT:
#    • If you copy, fork, or include this plugin in your own bot,
#      you MUST keep this header intact.
#    • You MUST give proper credit to the CipherElite Userbot author:
#        – GitHub:    https://github.com/rishabhops/CipherElite
#        – Telegram:  @thanosceo
#
#  Thank you for respecting open-source software!
# =============================================================================


import asyncio
from telethon import events, errors
from telethon.tl.types import User, Chat, Channel, MessageMediaWebPage
from utils.utils import CipherElite
from utils.decorators import rishabh
from plugins.bot import add_handler

# When True, `.gcast mylist` and `.gcast to` only send to broadcast channels;
# groups, supergroups and private users are skipped. Set False to allow them.
CHANNELS_ONLY = False

# Chats used by `.gcast mylist`. IDs in Telegram Web style (-1505914159) are
# converted to the full -100... form automatically. Edit this list as needed.
MY_CHATS = [
    "-1505914159",
    "-1564896319",
    "@ITOpenBookExam",
    "@filmzoneofficial",
    "-1544912526",
    "@MechOpenBookAnswers",
    "@Mech2013Answers",
    "-1430167518",
    "@AOEMOVIESCOLLECTIONS",
    "@R2017_au_open_book",
    "@fresher_jobs2026",
    "@annauniversity420",
    "-1633924130",
    "@aunotes_materials",
    "-1749161678",
    "-1646300858",
    "@ECEJOBSUPDATES",
    "@electronic_devi",
    "@supply_chain_au",
    "-1493690794",
    "@auopenbookexam_1styear",
    "@poojahegde07",
    "@IT2008Regulation",
    "@specialcaseexam",
    "-1478418812",
    "@OpenBookExamAnswer",
    "@Mech2017Answers",
    "@ecespecialcase",
    "-1432798059",
    "@akkaMcQuen",
    "-1355202730",
    "@signals_systems_au",
    "@mbaanswers",
    "@ECEOPENBOOK2017REGULATION",
    "-1561022154",
    "-1575759639",
    "-1550810737",
    "@webseries_gv",
    "-1502558591",
    "@samsinfoyt",
    "@santhanamcomedyclips",
]

def init(client_instance):
    """
    Required initialization function that registers commands and descriptions
    """
    commands = [
        ".gcast <target> [copy] - Broadcast message to all chats/groups/users with Cipher Elite engine"
    ]
    description = "📡 Cipher Elite Broadcast System - Advanced message broadcasting with intelligent targeting"
    add_handler("broadcast", commands, description)  # Short, professional button name

async def register_commands():
    """
    Cipher Elite broadcast system with advanced targeting
    """
    
    class CipherEliteBroadcastEngine:
        def __init__(self):
            self.broadcast_stats = {
                'sent': 0,
                'failed': 0,
                'total': 0,
                'errors': []
            }
            
        @staticmethod
        def is_admin(entity):
            """True if the account created the chat or is an admin in it.
            For broadcast channels, also require the right to post."""
            if getattr(entity, "creator", False):
                return True
            rights = getattr(entity, "admin_rights", None)
            if not rights:
                return False
            if isinstance(entity, Channel) and entity.broadcast:
                return bool(rights.post_messages)
            return True

        async def get_target_chats(self, client, target_type):
            """Get list of target chats based on type"""
            target_chats = []
            
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                
                if target_type == "all":
                    target_chats.append(entity)
                elif target_type == "groups":
                    # Basic groups (Chat) have no .broadcast attribute; only Channel does
                    if isinstance(entity, Chat) or (isinstance(entity, Channel) and not entity.broadcast):
                        target_chats.append(entity)
                elif target_type == "admin":
                    if isinstance(entity, (Chat, Channel)) and self.is_admin(entity):
                        target_chats.append(entity)
                elif target_type == "users":
                    if isinstance(entity, User) and not entity.bot:
                        target_chats.append(entity)
            
            return target_chats
        
        async def resolve_targets(self, client, refs):
            """Turn IDs / @usernames into chat entities.
            Returns (found, missing, skipped)."""
            await client.get_dialogs()  # fills Telethon's entity cache
            found, missing, skipped, seen = [], [], [], set()
            self.resolve_errors = {}
            for ref in refs:
                ref = str(ref).strip()
                candidates = []
                if ref.lstrip("-").isdigit():
                    n = int(ref)
                    if n < 0 and abs(n) < 10**12:
                        candidates.append(int(f"-100{abs(n)}"))  # Web-style channel/supergroup id
                    candidates.append(n)
                else:
                    candidates.append(ref if ref.startswith("@") else "@" + ref)
                entity = None
                for cand in candidates:
                    try:
                        entity = await client.get_entity(cand)
                        break
                    except Exception as e:
                        self.resolve_errors[ref] = type(e).__name__
                        continue
                if entity is None:
                    missing.append(ref)
                elif CHANNELS_ONLY and not (isinstance(entity, Channel) and entity.broadcast):
                    kind = "group/supergroup" if isinstance(entity, (Chat, Channel)) else "user/bot"
                    skipped.append(f"{ref} ({kind})")
                else:
                    key = (type(entity).__name__, entity.id)
                    if key not in seen:
                        seen.add(key)
                        found.append(entity)
                await asyncio.sleep(0.3)
            return found, missing, skipped

        @staticmethod
        def _name(chat):
            return (getattr(chat, "title", None)
                    or (("@" + chat.username) if getattr(chat, "username", None) else None)
                    or str(chat.id))

        async def _send_one(self, client, chat, message, use_forward):
            if use_forward:
                await client.forward_messages(chat, message)
            elif message.media and not isinstance(message.media, MessageMediaWebPage):
                await client.send_file(chat, message.media, caption=message.text or "")
            elif message.text:
                await client.send_message(chat, message.text)

        async def broadcast_message(self, client, message, target_chats, use_forward=True, status_msg=None):
            """Broadcast message to target chats"""
            self.broadcast_stats = {'sent': 0, 'failed': 0, 'total': len(target_chats), 'errors': []}
            
            for i, chat in enumerate(target_chats):
                try:
                    await self._send_one(client, chat, message, use_forward)
                    
                    self.broadcast_stats['sent'] += 1
                    
                    # Update status every 10 messages
                    if status_msg and (i + 1) % 10 == 0:
                        progress_percent = int((i + 1) / len(target_chats) * 100)
                        await status_msg.edit(
                            f"🎭 **Cipher Elite Broadcasting**\n\n"
                            f"📡 **Progress:** {progress_percent}%\n"
                            f"✅ **Sent:** {self.broadcast_stats['sent']}\n"
                            f"❌ **Failed:** {self.broadcast_stats['failed']}\n"
                            f"📊 **Total:** {self.broadcast_stats['total']}\n"
                            f"⚡ **Status:** Broadcasting in progress..."
                        )
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1.0)
                    
                except errors.FloodWaitError as e:
                    # Telegram asked us to slow down: wait, then retry this chat once
                    await asyncio.sleep(e.seconds + 1)
                    try:
                        await self._send_one(client, chat, message, use_forward)
                        self.broadcast_stats['sent'] += 1
                    except Exception:
                        self.broadcast_stats['failed'] += 1
                        self.broadcast_stats['errors'].append(self._name(chat))
                except Exception as e:
                    self.broadcast_stats['failed'] += 1
                    self.broadcast_stats['errors'].append(self._name(chat))
                    continue
            
            return self.broadcast_stats
    
    # Initialize broadcast engine
    broadcast_engine = CipherEliteBroadcastEngine()
    
    @CipherElite.on(events.NewMessage(pattern=r"\.gcast\s+(.+)"))
    @rishabh()
    async def cipher_elite_broadcast(event):
        try:
            if not event.reply_to_msg_id:
                await event.reply("🎭 **Cipher Elite Broadcast System**\n\n"
                                "❌ **Error:** Please reply to a message to broadcast!\n\n"
                                "**Usage:**\n"
                                "• `.gcast all` - Broadcast to all chats\n"
                                "• `.gcast groups` - Broadcast to groups only\n"
                                "• `.gcast users` - Broadcast to users only\n"
                                "• `.gcast admin` - Chats where you are admin\n"
                                "• `.gcast mylist` - Your saved list (MY_CHATS)\n"
                                "• `.gcast to <ids/@names>` - Only the chats you list\n"
                                "• `.gcast all copy` - Copy without forward tag\n\n"
                                "🤖 **Powered by Cipher Elite**")
                return
            
            # Parse command arguments
            args = event.pattern_match.group(1).split()
            
            if not args:
                await event.reply("❌ **Cipher Elite Error:** Please specify target (all/groups/users/admin/mylist/to)")
                return
            
            target_type = args[0].lower()
            
            if target_type not in ["all", "groups", "users", "admin", "mylist", "to"]:
                await event.reply("🎭 **Cipher Elite Broadcast Error**\n\n"
                                "❌ **Invalid target type!**\n\n"
                                "**Valid targets:**\n"
                                "• `all` - All chats\n"
                                "• `groups` - Groups only\n"
                                "• `users` - Users only\n"
                                "• `admin` - Chats where you are admin\n"
                                "• `mylist` - Your saved list\n"
                                "• `to <ids/@names>` - Only the chats you list\n\n"
                                "**Example:** `.gcast groups copy`")
                return
            
            # Check if copy mode is specified
            use_forward = True
            rest = args[1:]
            if rest and rest[-1].lower() == "copy":
                use_forward = False
                rest = rest[:-1]
            
            # Get replied message
            reply_message = await event.get_reply_message()
            
            if not reply_message:
                await event.reply("❌ **Cipher Elite Error:** Could not get replied message!")
                return
            
            # Initial status message
            status_msg = await event.reply("🎭 **Cipher Elite Broadcast System**\n\n"
                                         f"🎯 **Target:** {target_type.title()}\n"
                                         f"📋 **Mode:** {'Copy' if not use_forward else 'Forward'}\n"
                                         f"🔄 **Status:** Analyzing target chats...\n"
                                         f"⚡ **Engine:** Advanced Broadcasting Algorithm")
            
            # Get target chats
            unresolved = []
            skipped = []
            if target_type in ("mylist", "to"):
                if target_type == "mylist":
                    refs = MY_CHATS
                else:
                    refs = [r for a in rest for r in a.replace(",", " ").split()]
                if not refs:
                    await status_msg.edit("❌ **Cipher Elite Error:** Give at least one chat ID or @username after `to`")
                    return
                target_chats, unresolved, skipped = await broadcast_engine.resolve_targets(event.client, refs)
            else:
                target_chats = await broadcast_engine.get_target_chats(event.client, target_type)
            
            if not target_chats:
                detail = ""
                if skipped:
                    detail += "⏭️ **Skipped, not a channel:** " + ", ".join(skipped[:15]) + "\n"
                if unresolved:
                    errs = getattr(broadcast_engine, "resolve_errors", {})
                    detail += "⚠️ **Not found:** " + ", ".join(
                        f"{u} ({errs[u]})" if u in errs else u for u in unresolved[:15]) + "\n"
                await status_msg.edit("🎭 **Cipher Elite Broadcast Result**\n\n"
                                     f"❌ **No target chats found for type:** {target_type}\n"
                                     + detail +
                                     "💡 **Check the IDs/usernames, membership, and CHANNELS_ONLY**")
                return
            
            await status_msg.edit(f"🎭 **Cipher Elite Broadcasting**\n\n"
                                 f"🎯 **Target:** {target_type.title()}\n"
                                 f"📊 **Found:** {len(target_chats)} chats\n"
                                 f"📋 **Mode:** {'Copy' if not use_forward else 'Forward'}\n"
                                 f"🚀 **Starting broadcast...**\n"
                                 f"⚡ **Status:** Initializing...")
            
            # Start broadcasting
            stats = await broadcast_engine.broadcast_message(
                event.client, 
                reply_message, 
                target_chats, 
                use_forward, 
                status_msg
            )
            
            # Final results
            success_rate = int((stats['sent'] / stats['total']) * 100) if stats['total'] > 0 else 0
            
            result_msg = f"🎭 **Cipher Elite Broadcast Complete**\n\n"
            result_msg += f"📊 **Broadcast Statistics:**\n"
            result_msg += f"✅ **Successfully sent:** {stats['sent']}\n"
            result_msg += f"❌ **Failed:** {stats['failed']}\n"
            result_msg += f"📈 **Success rate:** {success_rate}%\n"
            result_msg += f"🎯 **Total targets:** {stats['total']}\n\n"
            result_msg += f"📋 **Target type:** {target_type.title()}\n"
            result_msg += f"🔧 **Mode:** {'Copy' if not use_forward else 'Forward'}\n\n"
            
            if success_rate >= 90:
                result_msg += f"🔥 **Status:** Excellent broadcast performance!\n"
            elif success_rate >= 70:
                result_msg += f"✅ **Status:** Good broadcast performance\n"
            elif success_rate >= 50:
                result_msg += f"⚠️ **Status:** Average broadcast performance\n"
            else:
                result_msg += f"❌ **Status:** Poor broadcast performance\n"
            
            if skipped:
                result_msg += f"⏭️ **Skipped, not a channel ({len(skipped)}):** " + ", ".join(skipped[:15]) + "\n\n"
            if unresolved:
                errs = getattr(broadcast_engine, "resolve_errors", {})
                result_msg += f"⚠️ **Not found ({len(unresolved)}):** " + ", ".join(
                    f"{u} ({errs[u]})" if u in errs else u for u in unresolved[:15]) + "\n\n"
            if stats.get('errors'):
                result_msg += f"❌ **Failed in:** " + ", ".join(stats['errors'][:15]) + "\n\n"
            result_msg += f"🤖 **Powered by Cipher Elite**"
            
            await status_msg.edit(result_msg)
            
        except Exception as e:
            await event.reply(f"🎭 **Cipher Elite Broadcast System Error**\n\n"
                            f"❌ **Critical Error:** {str(e)[:100]}...\n"
                            f"💡 **Suggestion:** Try again with valid parameters\n"
                            f"🔧 **Support:** Check your permissions and network")
    
    @CipherElite.on(events.NewMessage(pattern=r"\.bstats"))
    @rishabh()
    async def broadcast_stats(event):
        try:
            # Get chat statistics
            total_chats = 0
            groups_count = 0
            users_count = 0
            channels_count = 0
            
            async for dialog in event.client.iter_dialogs():
                entity = dialog.entity
                total_chats += 1
                
                if isinstance(entity, User) and not entity.bot:
                    users_count += 1
                elif isinstance(entity, Chat):
                    groups_count += 1
                elif isinstance(entity, Channel):
                    if entity.broadcast:
                        channels_count += 1
                    else:
                        groups_count += 1
            
            stats_msg = f"🎭 **Cipher Elite Broadcast Statistics**\n\n"
            stats_msg += f"📊 **Your Chat Distribution:**\n"
            stats_msg += f"👥 **Total chats:** {total_chats}\n"
            stats_msg += f"👤 **Users:** {users_count}\n"
            stats_msg += f"👥 **Groups:** {groups_count}\n"
            stats_msg += f"📢 **Channels:** {channels_count}\n\n"
            stats_msg += f"🎯 **Broadcast Targets:**\n"
            stats_msg += f"• `all` → {total_chats} chats\n"
            stats_msg += f"• `users` → {users_count} users\n"
            stats_msg += f"• `groups` → {groups_count} groups\n\n"
            stats_msg += f"🤖 **Cipher Elite Analytics**"
            
            await event.reply(stats_msg)
            
        except Exception as e:
            await event.reply(f"🎭 **Stats Error:** {str(e)}")
