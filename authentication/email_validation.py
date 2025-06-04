import re
import dns.resolver

DISPOSABLE_EMAIL_DOMAINS = [
    'mailinator.com', 'guerrillamail.com', 'temp-mail.org', 'tempmail.com', 'throwawaymail.com',
    'yopmail.com', 'mailnesia.com', 'trashmail.com', '10minutemail.com', 'fakeinbox.com', 'tempinbox.com',
    'sharklasers.com', 'dispostable.com', 'getnada.com', 'maildrop.cc', 'mohmal.com', 'f5url.com', 
    'tempail.com', 'mailforspam.com', 'spamgourmet.com', 'tempr.email', 'spamfree24.org', 'spamhereplease.com',
    'emailondeck.com', 'anonbox.net', 'nada.email', 'dropmail.me', 'mailinator.net', 'mailinator.org', 'mailsac.com',
    'tempmailaddress.com', 'tempinbox.co', 'mintemail.com', 'spamex.com', 'spamcero.com', 'jetable.org', 
    'get2mail.fr', 'dingbone.com', 'fakemail.net', 'emailtemporario.com.br', 'tempemail.co','burnermail.io',
    'temporarymail.com', 'temp-email.com', 'mytemp.email', 'temp-email.org', 'disposable.email', 'anonymize.com',
    'sofimail.com', 'incognitomail.com', 'tempmailo.com', 'mytrashmail.com', 'instant-mail.de', 'spamcowboy.com',
    'spamcowboy.net', 'spamcowboy.org', 'spam4.me', 'grr.la', 'guerrillamail.biz', 'guerrillamail.de', 
    'guerrillamail.net', 'guerrillamail.org', 'guerrillamailblock.com', 'spam.la', 'speedmail.de',
    'trbvm.com', 'harakirimail.com', 'gmailpro.ml', 'tmpmail.net', 'tmpmail.org', 'tmails.net', 'disbox.net', 
    'disbox.org', 'throam.com', 'vomoto.com', 'esiix.com', 'emlpro.com', 'emlhub.com', 'emltmp.com', 'powerencry.com', 
    'tmpbox.net', 'moakt.cc', 'moakt.co', 'moakt.ws', 'tmail.ws', 'bareed.ws', 'wimsg.com', 'linshiyou.com', 
    '1secmail.com', '1secmail.net', '1secmail.org', 'guerrillamail.info', 'spam4.me', 'mailmetrash.com', 'mailnull.com',
    'classic-emails.com', 'classicmail.co.za', 'tempsky.com', 'deemail.com', 'tempmail.space', 'eyepaste.com', 
    'fivemail.de', 'hidemail.de', 'gotmail.net', 'gotmail.org', 'hotpop.com', 'ieatspam.eu', 'mailexpire.com', 
    'mailforspam.com', 'mailin8r.com', 'mailinator.us', 'reallymymail.com', 'safetymail.info', 'spamspot.com', 
    'trashmail.net', 'deadaddress.com', 'filzmail.com', 'temp-mail.ru', 'tempmail.it', 'throwawaymail.ca','33mail.com',
    'abcmail.email', 'airmail.cc', 'alexbox.fr', 'antireg.com', 'antireg.ru', 'armyspy.com', 'aver.com', 'beefmilk.com', 
    'binkmail.com', 'bio-muesli.net', 'blurp.de', 'bobmail.info', 'boximail.com', 'burgas.vip', 'cektmail.com', 
    'cellurl.com', 'cheatmail.de', 'cocovpn.com', 'correotemporal.org', 'crazymailing.com', 'cust.in', 'cuvox.de', 
    'dayrep.com', 'dcctb.com', 'developermail.com', 'dextm.ro', 'dfgh.net', 'digitalsanctuary.com', 'discardmail.com', 
    'discardmail.de', 'disposableemailaddresses.com', 'disposableinbox.com', 'dispose.it', 'dm.w3internet.co.uk', 
    'duck2.club', 'dumpmail.de', 'dumpyemail.com', 'e4ward.com', 'easytrashmail.com', 'einrot.com', 'email-fake.com', 
    'emailage.com', 'emaildrop.io', 'emailfake.com', 'emailgo.de', 'emailias.com', 'emailna.co', 'emailo.pro', 
    'emailsensei.com', 'emailtemp.org', 'emailtmp.com', 'emailto.de', 'emailwarden.com', 'emailx.at.hm', 'emiltmp.in', 
    'enterto.com', 'ephemail.net', 'evopo.com', 'explodemail.com', 'fakemailgenerator.com', 'fakemailz.com', 'fammix.com', 
    'fightallspam.com', 'flurred.com', 'fomillio.net', 'freenom.com', 'fuzzymail.org', 'getairmail.com', 'getcoolmail.info', 
    'gettempemail.com', 'gigmail.com', 'gmal.com', 'gmx.us', 'gowikibooks.com', 'greencafes.org', 'haltospam.com', 
    'hebos.online', 'hour.email', 'hulapla.de', 'ichmail.pw', 'imgof.com', 'imstations.com', 'incognitosurfing.pro', 
    'inoutmail.de', 'instantemailaddress.com', 'into.id.au', 'ipoo.org', 'irish2me.com', 'iwi.net', 'jnxjn.com', 
    'junkmail.com', 'killmail.com', 'kingsq.ga', 'lazyinbox.com', 'leeching.net', 'letthemeatspam.com', 'lol.ovpn.to', 
    'lookugly.com', 'lroid.com', 'luxusmail.cf', 'mailde.de', 'mailhazard.com', 'mailhz.me', 'mailkept.com', 'mailnator.com', 
    'mailslite.com', 'mailtemp.io', 'mailtome.de', 'mailzi.ru', 'meltmail.com', 'messagebeamer.de', 'mierdamail.com', 
    'migumail.com', 'minex-coin.com', 'miodonios.com', 'mmmmail.com', 'mobi.web.id', 'muimail.com', 'mymail-in.net', 
    'mymailoasis.com', 'netpmail.com', 'nomail.ch', 'nomail.net', 'nowmymail.com', 'objectmail.com', 'oopi.org', 
    'orangatango.com', 'otherinbox.com', 'ourklips.com', 'pancakemail.com', 'pokemail.net', 'politikerclub.de', 
    'pooae.com', 'poofy.org', 'porco.cf', 'postacin.com', 'privacy.net', 'privatdemail.net', 'proxymail.eu', 'punkass.com', 
    'putthisinyourspamdatabase.com', 'qq.com', 'quickinbox.com', 'radiku.ye.vc', 'rcpt.at', 'receiveee.com', 'rhyta.com', 
    'rklips.com', 'schafmail.de', 'secmail.pw', 'secure-mail.biz', 'secure-mail.cc', 'selfdestructingmail.com', 'sendspamhere.com', 
    'shitaway.cf', 'shitmail.de', 'shitmail.me', 'shitmail.org', 'shortmail.net', 'slopsbox.com', 'smap.4nmv.ru', 
    'smashmail.de', 'smellfear.com', 'sneakemail.com', 'snkmail.com', 'solarino.ru', 'spambox.info', 'spambox.me', 
    'spambox.us', 'spamcannon.com', 'spamcannon.net', 'spamcon.org', 'spamday.com', 'spamfree.eu', 'spamgoes.in', 
    'spamherelots.com', 'spamify.com', 'spaml.com', 'spammotel.com', 'spamobox.com', 'spamslicer.com', 'spamthis.co.uk', 
    'spamthisplease.com', 'spikio.com', 'spoofmail.de', 'squizzy.de', 'sry.li', 'stexsy.com', 'streetwisemail.com', 
    'super-auswahl.de', 'superplatyna.com', 'superstachel.de', 'tafmail.com', 'tempinbox.me', 'tempomail.fr', 'temporarily.de', 
    'temporaryemail.net', 'temporary-mail.net', 'tempymail.com', 'thankme.net', 'thisisnotmyrealemail.com', 'thrma.com', 
    'tilien.com', 'tmail.com', 'tmailinator.com', 'toiea.com', 'tongud.com', 'trash-mail.at', 'trash-mail.cf', 
    'trash-mail.com', 'trash-mail.de', 'trash-mail.ga', 'trash-mail.gq', 'trash-mail.ml', 'trash-mail.tk', 
    'trashdevil.com', 'trashdevil.de', 'trashemail.de', 'trashinbox.com', 'trashmail.at', 'trashmail.com', 'trashmail.de', 
    'trashmail.io', 'trashmail.me', 'trashmail.net', 'trashmailer.com', 'trashymail.com', 'trbvn.com', 'tutanota.com', 
    'twinmail.de', 'tyldd.com', 'uggsrock.com', 'upliftnow.com', 'venompen.com', 'veryrealemail.com', 'vfemail.net', 
    'vickaentb.com', 'vidchart.com', 'viditag.com', 'viewcastmediae', 'vinbazar.com', 'visible.link', 'vomoto.com', 
    'walala.org', 'walkmail.ru', 'we.qq.com', 'webemail.me', 'webm4il.info', 'webuser.in', 'wegwerfadresse.de', 
    'wegwerfemail.com', 'wegwerfemail.de', 'wegwerf-email-addressen.de', 'wegwerf-emails.de', 'wegwerfmail.de', 
    'wegwerfmail.info', 'wegwerfmail.net', 'wegwerfmail.org', 'wetrainbayarea.com', 'wetrainbayarea.org', 'wh4f.org', 
    'whatiaas.com', 'whatsaas.com', 'whopy.com', 'wickmail.net', 'willhackforfood.biz', 'willselfdestruct.com', 
    'winemaven.info', 'wolfsmail.tk', 'writeme.us', 'wronghead.com', 'wuzup.net', 'wuzupmail.net', 'ychatz.com', 
    'yroid.com', 'yugasandrika.com', 'z1p.biz', 'za.com', 'zain.site', 'zainmax.net', 'zeitfenster.org', 
    'zippymail.info', 'zoaxe.com', 'zoemail.net', 'zoemail.org', 'zomg.info', 'example.com'
]

def validate_email_domain(email):
    """Validate email by checking if domain has valid MX records"""
    domain = email.split('@')[-1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        return False

def is_disposable_email(email):
    """Check if email is from a known disposable domain"""
    domain = email.split('@')[-1].lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS

def is_valid_email_format(email):
    """Check if email has valid format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))