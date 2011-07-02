#!/bin/env python
'''
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
  MA 02110-1301, USA.

A GUI to edit a single book.
TODO: Add logic for new new borrows table.
  Fix logic for borrowers list and checkbox.  If borrowed, ONLY the borrower
  should appear in the list and the checkbox should ALWAYS reflect correct status.
'''

import MySQLdb
import sys
import ConfigParser
import logging
import gtk
import pygtk
from biblio.webquery.xisbn import XisbnQuery
import biblio.webquery
import book
import load_config
import copy
import gettext


_ = gettext.gettext

logger = logging.getLogger("barscan")
logging.basicConfig(format='%(module)s: LINE %(lineno)d: %(levelname)s: %(message)s:', level=logging.DEBUG)

config = load_config.load_config()
db_user = config.db_user
db_pass = config.db_pass
db_base = config.db_base
db_host = config.db_host

##################BEGIN add_edit class #################################
class add_edit:
  def __init__(self):
    self.borrowers = 0
    builder = gtk.Builder()
    builder.add_from_file("ui/edit_book.glade")
    builder.connect_signals(self)
    self.window = builder.get_object("window_edit")
    self.isbn =  builder.get_object("entry1")
    self.author =  builder.get_object("entry2")
    self.title =  builder.get_object("entry3")
    self.publisher =  builder.get_object("entry4")
    self.year =  builder.get_object("entry5")
    self.city =  builder.get_object("entry6")
    self.abstract =  builder.get_object("entry7")
    self.mtype =  builder.get_object("entry8")
    self.copies = builder.get_object("entry9")
    self.lent = builder.get_object("checkbutton1")
    self.lentlist = builder.get_object("liststore1")
    self.lent_select = builder.get_object("comboboxentry1")
    self.where = ""
    self.mybook = book.book()
    self.orig_book = book.book()
    self.status = builder.get_object("label_status")
    self.lent_date = builder.get_object("b_date")

    #col = gtk.comboboxentry()
    self.lent_select.set_model( self.lentlist)
    self.lent_select.set_text_column(1)

    self.o_date = ''

    try:
        self.db = MySQLdb.connect(host = db_host, db=db_base,  passwd = db_pass);
    except:
      print _("No database connection.  Check ") + config_file
      self.db = False
    if self.db:
      self.cur = self.db.cursor()

  def display(self):
    gtk.main()
    pass

  def on_destroy(self,widget):
    if __name__ == "__main__":
      gtk.main_quit()
    else:
      self.window.hide()
      pass


  def isbn_lookup(self,widget):
    ''' Lookup the book on XisbnQuery
    returns biblio.webquery.bibrecord.BibRecord
    update the database and close the window
    '''
    a = XisbnQuery()
    try:
      abook = a.query_bibdata_by_isbn(self.isbn.get_text())
      nn = abook.pop()
      self.isbn.set_text(nn.id)
      self.title.set_text(nn.title)
      self.author.set_text(str(nn.authors))
      self.abstract.set_text(nn.abstract)
      self.mtype.set_text(nn.type)
      self.publisher.set_text(nn.publisher)
      self.city.set_text(nn.city)
      self.year.set_text(nn.year)
    except:
      logging.info_("No book found")
      d = gtk.Dialog()
      d.add_buttons(gtk.STOCK_OK, 1)
      label = gtk.Label(_('No Book found for this ISBN!'))
      label.show()
      d.vbox.pack_start(label)
      d.run()
      d.destroy()

    self.update_book()

  def populate_borrowers(self):
    ''' Get borrowers and fill in the list'''

    pass

  def populate(self,book_id):
    cur = self.db.cursor(MySQLdb.cursors.DictCursor)
    cur.execute ("SELECT * FROM  books where id = %s;",book_id)
    result = cur.fetchall()
    #logging.info(result)
    for row in result:
      # Populate GUI
      self.isbn.set_text(row['isbn'])
      self.author.set_text(row['author'])
      self.title.set_text(row['title'])
      self.abstract.set_text(row['abstract'])
      self.publisher.set_text(row['publisher'])
      self.city.set_text(row['city'])
      self.year.set_text(str(row['year']))
      self.copies.set_text(str(row['copies']))

      # Populate a book object
      self.orig_book.isbn =row['isbn']
      self.orig_book.id = row['id']
      self.orig_book.authors = row['author']
      self.orig_book.title = row['title']
      self.orig_book.abstract = row['abstract']
      self.orig_book.publisher = row['publisher']
      self.orig_book.city = row['city']
      self.orig_book.year = row['year']
      self.orig_book.copies = row['copies']
      self.orig_book.where = row['location']

      self.mybook = copy.copy(self.orig_book)

    #Populate borrowers combo box etc.
    self.cur.execute ("SELECT * FROM  borrowers;")
    result = self.cur.fetchall()
    for row in result:
      self.lentlist.append([row[0], row[1], row[2]])
      self.lent_select.append_text(row[1])
      self.borrowers += 1
    #Get borrows for this book up to the # of copies
    # NB. Need to track copies available for borrowing
    self.cur.execute("SELECT * FROM borrows where book = %s AND i_date IS NULL AND o_date IS NOT NULL LIMIT %s;",
          [self.orig_book.id,self.orig_book.copies])
    result = self.cur.fetchall()
    bid = 0
    for row in result:
      bid = row[4]
      book_id = row[3]
      self.o_date = row[1]
    if bid != 0:
      logging.info(bid)
      if self.orig_book.id == book_id:
        self.orig_book.copies -=1
        self.copies.set_text(str(self.orig_book.copies))
      # Set active to current borrower.
      self.lent_select.set_active(bid - 1)
      self.lent_date.set_text(str(self.o_date))
    else: self.lent_select.set_active(0)
    '''
    if self.orig_book.where == 0:
      self.lent.set_active(False)
      self.lentlist.append([0, '', ''])
    else:
      self.lent.set_active(True)
    del cur
    '''


  def update_book(self):
    ## Update any changes from GUI
    self.mybook.isbn=self.isbn.get_text()
    self.mybook.title=self.title.get_text()
    self.mybook.authors=self.author.get_text()
    self.mybook.abstract=self.abstract.get_text()
    #self.mybook.mtype=self.mtype.get_text()
    self.mybook.publisher=self.publisher.get_text()
    self.mybook.city=self.city.get_text()
    self.mybook.year=self.year.get_text()

    #logging.info(self.mybook.year)
    # Is the book on loan and to whome?

  def on_button_update_clicked(self, widget):
    ''' Update the database with new info or add if not already in.'''
    self.update_book()
    self.update_db()
    pass



  def update_db(self):
    book = self.mybook
    #logging.info(self.orig_book.compare(book))
    result = self.cur.execute ("SELECT * FROM books WHERE isbn = %s;",book.isbn)
    #logging.info(result)
    if result == 0: # If no book in DB, add it
    # Make sure we don't add an empty book.  We could also use this to check for changes if we have a copy of the original data.
      book_data = book.title + book.authors + book.isbn + book.abstract + book.year + book.publisher + book.city
      logging.info(book_data)
      if book_data == '': return # Do nothing if no data
      if not isdigit(book.year): book.year = 0 #DB query fix for empty date field.
      self.cur.execute("INSERT INTO books(title, author, isbn,abstract, year, publisher, city, copies) \
      VALUES(%s, %s, %s,%s,%s,%s,%s,%s);", \
      (book.title, book.authors, book.isbn, book.abstract,book.year,book.publisher,book.city, 1))
      self.status.set_text(_(" Book has been inserted."))

    elif  self.orig_book.compare(book) != 0:
      logging.info("Somthing changed so an update is needed")
      self.update_book()
      self.cur.execute("UPDATE books SET title = %s, author = %s,abstract = %s, year = %s, publisher = %s, city = %s WHERE isbn = %s", \
      (book.title, book.authors, book.abstract,book.year,book.publisher,book.city, book.isbn))
      self.db.commit()
      self.status.set_text(_(" Book has been updated."))
      self.mybook = copy.copy(self.orig_book)

  def on_button_remove_clicked(self, widget):
    ''' Remove selected book from database '''
    return
    self.update_book()
    #logging.info(str(self.mybook.id) + " about to be removed.")
    self.cur.execute("UPDATE books set copies = copies-1 WHERE isbn = %s;",self.mybook.id)
    self.status.set_text (_(" Book has been removed."))
    self.db.commit()


  def on_comboboxentry1_changed(self,widget):
    ''' Do things when selection is changed
    Need to check if the selected borrower has the book and set the checkbutton status to suit '''
    foo = self.lent_select.get_active()
    bid = self.lentlist[foo][0]
    # Get list of borrows for this book
    result = self.cur.execute("SELECT * FROM borrows where borrows.book = %s AND borrower = %s AND i_date IS NULL AND o_date IS NOT NULL;" ,
        [self.mybook.id,bid])
    #logging.info(result)
    if result == 0:
      self.lent.set_active(False)
    else:
       self.lent.set_active(True)


  def on_button_clear_clicked(self, widget):
    ''' Clear all the edit boxes '''
    self.isbn.set_text('')
    self.author.set_text('')
    self.title.set_text('')
    self.abstract.set_text('')
    self.publisher.set_text('')
    self.city.set_text('')
    self.year.set_text('')
    self.copies.set_text('')


  def on_checkbutton1_toggled(self, widget):
    #logging.info(widget)
    # Get widget state
    # Set book as borrowed or not with borrower as key
    if self.lent.get_active(): # Checked
      foo = self.lent_select.get_active()
      bid = self.lentlist[foo][0]
      #logging.info(bid)
      if bid != 0 and self.mybook.id != 0 and self.orig_book.copies > 0:
        self.cur.execute("INSERT INTO borrows(book, borrower, o_date) SELECT %s, %s, now() FROM DUAL WHERE NOT EXISTS(SELECT 1 FROM borrows WHERE book = %s AND borrower = %s AND i_date IS NULL);",
            [self.mybook.id, bid,self.mybook.id, bid])
        self.db.commit()
        self.status.set_text(_("Book has been marked as borrowed."))
        self.orig_book.copies -= 1
      else:
        self.status.set_text(_("Book has been NOT marked as borrowed."))
        #self.lent.set_active(False)
      self.lent_date.set_text(str(self.o_date))

    else: # Unchecked
      self.lent_date.set_text(str(""))
      foo = self.lent_select.get_active()
      bid = self.lentlist[foo][0]
      if bid != 0:
        result = self.cur.execute("UPDATE borrows SET i_date = NOW() WHERE book = %s AND borrower = %s AND i_date IS NULL",
          [self.mybook.id, bid])
        self.db.commit()
        if result:
          self.orig_book.copies += 1
          self.status.set_text(_("Book has been marked as returned."))
        else: self.status.set_text(_("Book has been NOT marked as returned."))
    self.copies.set_text(str(self.orig_book.copies))


############## END add_edit class ######################################
# For testing or stand alone
if __name__ == "__main__":
  app = add_edit()
  app.display()

